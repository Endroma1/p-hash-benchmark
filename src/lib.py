from itertools import product, starmap
from re import sub
from typing import Callable, Optional, Iterator, TextIO
from PIL import Image
from pathlib import Path
from queue import Empty

from hash_methods import AverageHash
from hash_image import HashJobBuilder, HashMethod, ImageHash
from pickle_img import PickleableImage
from modify_image import Base, ModImage, ModImageBuilder, Modification
from modify_methods import Flip
from matching import MatchingProcess, MatchResult
from multiprocessing import Event, Process, Queue, Pool, current_process
from result_calc import Roc
from config import BenchmarkConfig
import logging

from sqlite_imghash import ImgHashDB, UserPathsQueuer
from multiprocess_tools import STOP, StopSignal


logging.basicConfig(filename="app.log", level=logging.DEBUG, filemode="w")


class Benchmark:
    """Benchmarks one hashing method"""

    def __init__(
        self,
        hash_method: type[HashMethod],
        image_paths: list[Path],
        mods: list[type[Modification]],
        db_fetchers: int,
        img_openers: int,
        img_modifiers: int,
        img_hashers: int,
        result_calculators: int,
        all_users: bool,
        users: list[Path],
    ) -> None:
        self.method = hash_method
        self.input_images = image_paths
        self.mods = mods

        self.db_fetchers = db_fetchers
        self.img_openers = img_openers
        self.img_modifiers = img_modifiers
        self.img_hashers = img_hashers
        self.result_calculators = result_calculators

        self.all_users = all_users
        self.users = users

    def benchmark(self):
        q_paths: "Queue[Path | StopSignal]" = Queue()
        q_imgs: "Queue[PickleableImage | StopSignal]" = Queue()
        q_mods: "Queue[PickleableImage | StopSignal]" = Queue()
        q_hashes: "Queue[ImageHash | StopSignal]" = Queue()

        # [q_paths.put(p) for p in self.input_images]
        # [q_paths.put(STOP) for _ in range(self.img_openers)]

        fetcher = ImgHashDB().get_user_paths_to_queue(self.db_fetchers, q_paths)

        openers = [
            Process(target=self._open_imgs, args=(q_paths, q_imgs))
            for _ in range(self.img_openers)
        ]

        modifiers = [
            Process(target=self._modify_imgs, args=(q_imgs, q_mods))
            for _ in range(self.img_modifiers)
        ]

        hashers = [
            Process(target=self._hash_imgs, args=(q_mods, q_hashes))
            for _ in range(self.img_hashers)
        ]

        fetcher.start()

        for p in openers + modifiers + hashers:
            p.start()

        fetcher.join(self.img_openers)
        print("Db fetchers done")

        print("Waiting for image openers")
        for p in openers:
            p.join()
        print("Img openenrs done")

        logging.info("Opened all images")
        [q_imgs.put(STOP) for _ in range(self.img_modifiers)]

        for p in modifiers:
            p.join()

        print("Img modifiers done")

        logging.info("modified all images")
        [q_mods.put(STOP) for _ in range(self.img_hashers)]

        for p in hashers:
            p.join()

        print("Img hashers done")
        logging.info("hashed all images")
        result: list[MatchResult] = []

        while not q_hashes.empty():
            hash = q_hashes.get()
            if isinstance(hash, StopSignal):
                return None
            match_result = MatchingProcess(hash)
            match_result.save_results()
            result.extend(match_result.match_results)

        print("Calculating roc")
        Roc(result, self.method._name)

    def _open_imgs(self, paths: "Queue[Path | object]", imgs: "Queue"):
        while True:
            path = paths.get()

            if isinstance(path, StopSignal):
                break

            try:
                assert isinstance(path, Path)
            except Exception as e:
                logging.error(
                    f"Invalid value in open_img queue. Got value {path}, expected path or STOP signal. {e}"
                )
                continue

            try:
                img = Image.open(path)
            except Exception as e:
                logging.error(
                    f"Error opening image {path} in process: {current_process().name} for Benchmark::_open_imgs, {e}"
                )
                continue

            pickleable = PickleableImage.from_pil_image(img, path)
            imgs.put(pickleable)

    def _modify_imgs(
        self, imgs: "Queue[PickleableImage | StopSignal]", mod_imgs: "Queue"
    ) -> None:
        while True:
            pickleable = imgs.get()

            if isinstance(pickleable, StopSignal):
                break

            try:
                assert isinstance(pickleable, PickleableImage)
            except Exception as e:
                logging.error(
                    f"Invalid value in modify_imgs queue. Got value {pickleable}, expected PickleableImage or STOP signal. {e}"
                )
                continue

            path = pickleable.path
            img = pickleable.to_pil_image()

            try:
                modified_imgs: list[ModImage] = (
                    ModImageBuilder(img).set_mods(self.mods).run()
                )
            except Exception as e:
                logging.error(f"Error modifying image, {e}")
                continue

            for modify_img in modified_imgs:
                pickle = PickleableImage.from_pil_image(modify_img.image, path)
                mod_imgs.put(pickle)

    def _hash_imgs(
        self,
        imgs: "Queue[PickleableImage | StopSignal]",
        hashes: "Queue[ImageHash | StopSignal]",
    ) -> None:
        while True:
            pickleable = imgs.get()

            if isinstance(pickleable, StopSignal):
                break

            try:
                assert isinstance(pickleable, PickleableImage)
            except Exception as e:
                logging.error(
                    f"Invalid value in hash_imgs queue. Got value {pickleable}, expected PickleableImage or STOP signal. {e}"
                )
                continue

            path = pickleable.path
            img = pickleable.to_pil_image()

            assert isinstance(path, Path)

            try:
                hash = (
                    HashJobBuilder()
                    .set_img(img)
                    .set_method(self.method)
                    .set_img_path(path)
                    .build_hash_obj()
                )
            except Exception as e:
                logging.error(
                    f"Could not hash image with method {self.method.__name__}, {e}"
                )
                continue
            hashes.put(hash)


class BenchmarkBuilder:
    def __init__(
        self,
        image_paths: Optional[list[Path]] = None,
        mods: list[type[Modification]] = [Base, Flip],
        hash_method: type[HashMethod] = AverageHash,
        db_fetchers: int = 1,
        img_openers: int = 1,
        img_modifiers: int = 1,
        img_hashers: int = 1,
        result_calculators: int = 1,
        all_users: bool = True,
        users: list[Path] = [],
    ) -> None:
        self.method = hash_method
        self.input_images = image_paths
        self.mods = mods

        self.db_fetchers = db_fetchers
        self.img_openers = img_openers
        self.img_modifiers = img_modifiers
        self.img_hashers = img_hashers
        self.result_calculators = result_calculators
        self.all_users = all_users
        self.users = users

    def set_image_paths(self, image_paths: list[Path]) -> "BenchmarkBuilder":
        self.input_images = image_paths
        return self

    def set_image_paths_with_dir(self, dir_path: Path) -> "BenchmarkBuilder":
        if not dir_path.is_dir():
            raise ValueError(
                f"BenchmarkBuilder with dir did not take dir. Path:{dir_path}"
            )

        paths = [p for p in dir_path.rglob("*") if p.is_file()]

        if paths is None:
            raise ValueError(
                f"BenchmarkBuilder with dir did not find any files. Check {dir_path}"
            )

        self.input_images = paths
        return self

    def set_mods(self, mods: list[type[Modification]]) -> "BenchmarkBuilder":
        self.mods = mods
        return self

    def set_hash_method(self, hash_method: type[HashMethod]) -> "BenchmarkBuilder":
        self.method = hash_method
        return self

    def set_img_openers(self, img_openers: int) -> "BenchmarkBuilder":
        self.img_openers = img_openers
        return self

    def set_db_fetchers(self, db_fetchers: int) -> "BenchmarkBuilder":
        self.db_fetchers = db_fetchers
        return self

    def set_img_modifiers(self, img_modifiers: int) -> "BenchmarkBuilder":
        self.img_modifiers = img_modifiers
        return self

    def set_img_hashers(self, img_hashers: int) -> "BenchmarkBuilder":
        self.img_hashers = img_hashers
        return self

    def set_result_calculators(self, result_calculators: int) -> "BenchmarkBuilder":
        self.result_calculators = result_calculators
        return self

    def set_all_users(self, all_users: bool) -> "BenchmarkBuilder":
        self.all_users = all_users
        return self

    def set_users(self, users: list[Path]) -> "BenchmarkBuilder":
        self.users = users
        return self

    def run(self):
        if self.input_images is None:
            raise ValueError("BenchmarkBuilder did not receive input_paths")

        logging.info(
            "Starting benchmark with method=%s, input_images=%d images, mods=%s, "
            "img_openers=%d, img_modifiers=%d, img_hashers=%d, result_calculators=%d",
            (
                self.method.__name__
                if hasattr(self.method, "__name__")
                else str(self.method)
            ),
            len(self.input_images),
            [
                mod.__name__ if hasattr(mod, "__name__") else str(mod)
                for mod in self.mods
            ],
            self.img_openers,
            self.img_modifiers,
            self.img_hashers,
            self.result_calculators,
        )
        Benchmark(
            self.method,
            self.input_images,
            self.mods,
            self.db_fetchers,
            self.img_openers,
            self.img_modifiers,
            self.img_hashers,
            self.result_calculators,
            self.all_users,
            self.users,
        ).benchmark()

    @classmethod
    def from_config(cls, config: BenchmarkConfig):
        for hash_method in config.hashing_methods:
            (
                BenchmarkBuilder()
                .set_hash_method(hash_method)
                .set_mods(list(config.modifications))
                .set_image_paths_with_dir(config.input_path)
                .set_img_openers(config.img_open_procs)
                .set_img_hashers(config.hash_procs)
                .set_img_modifiers(config.mod_procs)
                .run()
            )


class DbGen:
    def __init__(
        self,
        path: Path,
        method: type[HashMethod],
        img_openers: int = 1,
        img_hashers: int = 1,
    ) -> None:
        if path.is_file():
            self._paths = [path]
        elif path.is_dir():
            self._paths = [p for p in path.rglob("*") if p.is_file()]

        self._img_openers = img_openers
        self._img_hashers = img_hashers
        self._method = method

    def dbgen(self):
        q_paths = Queue()
        q_imgs = Queue()
        q_hashes = Queue()

        openers = [
            Process(target=self._open_img, args=(q_paths, q_imgs))
            for _ in range(self._img_openers)
        ]

        hashers = [
            Process(target=self._hash_img, args=(q_imgs, q_hashes))
            for _ in range(self._img_hashers)
        ]

        [q_paths.put(p) for p in self._paths]
        [q_paths.put(STOP) for _ in range(self._img_openers)]

        for p in openers + hashers:
            p.start()

        for p in openers:
            p.join()

        [q_imgs.put(STOP) for _ in range(self._img_hashers)]

        for p in hashers:
            p.join()

        hashes: list[ImageHash] = []
        while not q_hashes.empty():
            try:
                hashes.append(q_hashes.get())
            except Empty:
                break

        [h.save_to_db() for h in hashes]

    def _open_img(self, q_paths: Queue, q_output: Queue) -> Optional[Image.Image]:
        while True:
            path = q_paths.get()

            if isinstance(path, StopSignal):
                break

            try:
                with Image.open(path) as i:
                    img = PickleableImage.from_pil_image(i, path)
                    q_output.put(img)
            except Exception as e:
                logging.error(f"img {path} could not be opened, {e}")
                continue

    def _hash_img(self, q_imgs: Queue, q_hashes: Queue):
        while True:
            pickleable: PickleableImage | StopSignal = q_imgs.get()

            if isinstance(pickleable, StopSignal):
                break

            path: Optional[Path] = pickleable.path

            if path is None:
                continue

            img: Image.Image = pickleable.to_pil_image()

            try:
                hash: ImageHash = (
                    HashJobBuilder()
                    .set_img(img)
                    .set_img_path(path)
                    .set_method(self._method)
                    .build_hash_obj()
                )
                q_hashes.put(hash)
            except Exception as e:
                logging.error(f"Could not hash image, {e}")
                continue
