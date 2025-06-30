from typing import Optional, TextIO, TypeVar
import toml
from abc import ABC, abstractmethod
from pathlib import Path

DEFAULT_TOML_FILE = Path.cwd() / "config.toml"


class TomlFile(ABC):
    def __init__(self, data) -> None:
        self.data = data

    @abstractmethod
    def dump(self, f, data):
        pass

    @classmethod
    @abstractmethod
    def create_default(cls) -> "TomlFile":
        pass

    @classmethod
    @abstractmethod
    def read_file(cls) -> "TomlFile":
        pass


class ConfigFile(TomlFile):
    def dump(self, f, data):
        toml.dump(f, data)

    @classmethod
    def create_default(cls) -> "ConfigFile":

        entry = {
            "benchmark": {
                "threads": 4,
            },
            "output": {"path": None},
            "hashing_methods": ["AverageHash"],
            "modifications": ["flipped"],
        }

        with open(DEFAULT_TOML_FILE) as f_out:
            toml.dump(entry, f_out)

        return cls(entry)

    @classmethod
    def read_file(cls) -> "ConfigFile":
        with open(DEFAULT_TOML_FILE) as f_in:
            entry = toml.load(f_in)

        return cls(entry)
