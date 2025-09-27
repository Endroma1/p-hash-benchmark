import argparse
from pathlib import Path

from .args_interface import SubCommand
from .args_errors import ArgumentNotGivenToParser, ConfigError
import sys

from config import BenchmarkConfig, ConfigInterface
from lib import BenchmarkBuilder


class Benchmark(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.subparser = subparser
        self._arguments()

    def _arguments(self):
        parser = self.subparser.add_parser(
            "benchmark", help="Benchmarks the given hashing methods"
        )
        parser.add_argument("-c", "--config", type=str, help="Path to config")

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        print("Parse")
        try:
            config_path: Path = args.config or ConfigInterface.default_config_path()
        except Exception as e:
            raise ConfigNotGiven()

        print("Read fili")
        try:
            config: BenchmarkConfig = ConfigInterface.read_file(config_path)
        except FileNotFoundError:
            raise ConfigNotFound(config_path)
        except Exception as e:
            raise ConfigError(e)

        try:
            BenchmarkBuilder.from_config(config)
        except Exception as e:
            raise BenchmarkError(e)


class ConfigNotGiven(Exception):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "Config not given or config not found from default path"

class ConfigNotFound(Exception):
    def __init__(self, path:Path) -> None:
        self.path = path
        pass

    def __str__(self) -> str:
        return f"Config from path {self.path} could not be found"

class BenchmarkError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"BenchmarkError: {self.error}"
