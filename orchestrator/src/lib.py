from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable, Optional, TypeVar 
from . import config
import asyncio
import httpx
from pydantic import BaseModel
import logging
from enum import Enum

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

CONFIG = config.Config.from_env()

@dataclass
class HealthCheckError(Exception):
    component_name:str
    def __str__(self) -> str:
        return f"Failed healthcheck for {self.component_name}"

class ComponentResponse(BaseModel):
    pass

class LoadResponse(ComponentResponse):
    id: int
    path: str
    user_id: int

class ModifiedImageResponse(ComponentResponse):
    id: int
    path: str
    image_id:int
    modification_id:int

class HashResponse(ComponentResponse):
    id:int
    hash:str
    mod_img_id:int
    hash_method_id:int

class MatchState(str, Enum):
    DONE = "done"
    IN_PROGRESS = "in progress"
    FAILED = "failed"
    STOPPED = "stopped"

class MatchStatusResponse(ComponentResponse):
    state: MatchState
    processed: int

@dataclass
class Component:
    """
    Represents a p-hash component. Attempts to get the data from the component if health check succeeds.
    """
    url:str
    health_path:str
    response_type: type[ComponentResponse]
    response_key: str
    _client:httpx.AsyncClient|None = None

    async def start_output_queue(self, out_queue:asyncio.Queue[ComponentResponse], path:str, json:dict):
        """
        Starts the component and puts the result given by response_type into the output queue.
        """
        while True:
            logging.info(f"Started {self.url}")
            async for result in self.start_iter(path, json):
                logging.info(f"Putting {result} in out queue")
                await out_queue.put(result)

    async def start_io_queue(self, in_queue:asyncio.Queue[ComponentResponse], out_queue:asyncio.Queue, path:str, json_func:Callable[[ComponentResponse], dict]):
        """
        Starts the component, takes data from input and puts the result given by response_type into the output queue.

        json_func: A function that returns json as payload. MUST take a json/dict object as arg and return json/dict
        """

        logging.info(f"Started {self.url}")

        while True:
            response:ComponentResponse = await in_queue.get()
            logging.info(f"{self.url} component got {response} from queue")
            json:dict = json_func(response)

            async for result in self.start_iter(path, json):
                await out_queue.put(result)

    async def start_iter(self, path:str, json:dict|None = None)->AsyncGenerator[ComponentResponse]:
        """
        Checks health of the component. If it succeeds it starts yielding the responses from the component given by `response_type`
        calls:
        Calls self._get_post_iter which runs forever. Therefore, this function will also run forever unless ConnectError is raised.
        Yields ComponentResponse. If no response is received because no more data is to be found, it loops until it does.

        arguments:
        path: Path to endpoint on component
        json: json payload to component

        returns:
        Generator of componentresponses
        """
        if self._client is None:
            logging.info("Starting client")
            self._client = httpx.AsyncClient()

        assert self._client is not None

        await self.check_health()

        async for load in self._get_post_iter(path, json):
            if load is None:
                logging.info(f"No more {self.response_type.__name__} received from {self.url}.")
                await asyncio.sleep(10)
                continue

            yield load


    async def _get_post_iter(self,path:str,json:dict|None, retries = 5, interval = 5)->AsyncGenerator[ComponentResponse | None] :
        """
        Attempts to get response from component. 

        path: Path to enpoint on component
        json: json payload to component
        retries: How many times to retry if httpx.ConnectError is raised
        interval: Time between retries

        return: ComponentResponse or None if no components were received
        """
        assert self._client is not None

        tries = 0
        while True:
            try:
                logging.info(f"Posting to {self.url}{path} with json: \n{json}")
                resp = await self._client.post(f"{self.url}{path}",json=json, timeout=httpx.Timeout(10.0, connect=5.0))
            except httpx.ConnectError:
                tries +=1
                logging.warning(f"Could not find client {self.url}. Retrying... ({tries}/{retries})")
                await asyncio.sleep(interval)
                continue

            tries = 0

            logging.info(f"Got {resp} from {self.url}")

            result = resp.json()
            logging.info(result)

            items = result.get(self.response_key, [])

            if not items:
                logging.info(f"Nothing received by component {self.url}, data: {result}")
                yield None

            if isinstance(items, dict):
                items = [items]

            for item in result[self.response_key]:   
                yield self.response_type(**item)
            break

    async def check_health(self, retries = 10):
        """
        Health checks the client. Hangs until it succeeds. Fails if not succeeded by (retries * 5) seconds
        """
        if self._client is None:
            self._client = httpx.AsyncClient()

        assert self._client is not None

        health_retries = 1
        while True:
            try:
                logger.info(f"Checking health for {self.url}{self.health_path}")
                resp = await self._client.get(f"{self.url}{self.health_path}")
                logger.info(f"Got response {resp} from healthcheck")
            except httpx.ConnectError:
                logging.warning(f"Could not find client {self.url} for health check. Retrying...")
                await asyncio.sleep(5)
                continue
            except asyncio.CancelledError:
                logger.warning(f"Health check task was cancelled for {self.url}")
                raise

            result = resp.json()
            try:
                if result["status"] == "ok":
                    logging.info(f"Healthcheck succeded for {self.url}")
                    break
            except Exception as e:
                if health_retries > retries:
                    logging.error(f"Healthcheck failed for {self.url}")
                    raise HealthCheckError(self.response_type.__name__)
                logger.warning(f"Endpoint not found {e}, attempt {health_retries}/{retries} . Retrying...")
                health_retries += 1
            await asyncio.sleep(5)

    async def wait_until_done(
        self,
        path: str,
        status_key: str = "state",
        done_value: str = "done",
        interval: int = 5,
    ):
        """
        When awaited, stops execution until component returns no more data.
        """
        if self._client is None:
            self._client = httpx.AsyncClient()

        assert self._client is not None

        while True:
            resp = await self._client.get(f"{self.url}{path}")
            result = resp.json()

            state = result.get(status_key)
            logger.info(f"{self.url} status: {state}")

            if state == done_value:
                return

            if state == "failed":
                raise RuntimeError(f"{self.url} failed")

            await asyncio.sleep(interval)

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        assert self._client is not None
        await self._client.aclose()

#################
### FUNCTIONS ###
#################

async def main():
    await run_pipeline()
    logging.info("Pipeline done")


async def run_pipeline():
    loader = Component(CONFIG.loader_url, health_path="/load/health", response_type=LoadResponse, response_key="images")
    modifier = Component(CONFIG.modifier_url, health_path="/modify/health", response_type=ModifiedImageResponse, response_key="modified_images")
    hasher = Component(CONFIG.hasher_url, health_path="/hash/health", response_type=HashResponse, response_key="hashes")

    loader_q: asyncio.Queue[ComponentResponse]= asyncio.Queue(maxsize=100)
    mod_q: asyncio.Queue[ComponentResponse] = asyncio.Queue(maxsize=200)
    hash_q: asyncio.Queue[ComponentResponse] = asyncio.Queue(maxsize=300)

    def limit_json_mod(comp:ComponentResponse)->dict:
        """
        Returns the component in json along with limit
        """
        return {"image": comp.model_dump(),"limit": 10}

    def limit_json_hash(comp:ComponentResponse)->dict:
        """
        Returns the component in json along with limit
        """
        return {"modified_image": comp.model_dump(),"limit": 10}

    tasks = [
         loader.start_output_queue(loader_q, path="/load/next",json={"limit":10}),
         modifier.start_io_queue(loader_q, mod_q, path="/modify/next",json_func=limit_json_mod),
         hasher.start_io_queue(mod_q, hash_q, path="/hash/next",json_func=limit_json_hash),
    ]


    coros = list(map(asyncio.create_task, tasks))

    try:
        await asyncio.gather(*coros)
    except asyncio.CancelledError:
        for coro in coros:
            coro.cancel()
        await asyncio.gather(*coros, return_exceptions=True)

async def run_matching():
    logging.info("Starting matching")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CONFIG.matcher_url}/match/start")
        json = response.json()
        logging.info(f"Started matching: {json}")


if __name__ == "__main__":
    asyncio.run(main())
