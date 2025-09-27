from dataclasses import dataclass, replace
from typing import Optional
import toml
import os
import logging
import json
from pathlib import Path
from interfaces import HashMethod, Modification
from registries import HashMethods, Modifications
from hash_methods import AverageHash
from modify_methods import Base

DEFAULT_TOML_FILE = Path.cwd() / "config.toml"
DEFAULT_INPUT_PATH = Path.cwd() / "gruppens_test_bilder"
DEFAULT_HASHING_METHODS: tuple[type[HashMethod], ...] = (AverageHash,)
DEFAULT_MODIFICATIONS: tuple[type[Modification], ...] = (Base,)


@dataclass(frozen=True)
class BenchmarkConfig:
    # General
    input_path: Path = DEFAULT_INPUT_PATH

    hashing_methods: tuple[type[HashMethod], ...] = DEFAULT_HASHING_METHODS
    modifications: tuple[type[Modification], ...] = DEFAULT_MODIFICATIONS

    # Procs
    db_fetcher_procs: int = 1
    img_open_procs: int = 1
    mod_procs: int = 1
    hash_procs: int = 1

    def with_input_path(self, path: Optional[Path]):
        if path is None:
            return self
        return replace(self, input_path=path)

    def with_hashing_methods(self, methods: Optional[tuple[type[HashMethod], ...]]):
        if methods is None:
            return self
        return replace(self, hashing_methods=methods)

    def with_modifications(self, methods: Optional[tuple[type[Modification], ...]]):
        if methods is None:
            return self
        return replace(self, modifications=methods)

    def with_db_fetcher_procs(self, num: Optional[int]):
        if num is None:
            return self
        return replace(self, db_fetcher_procs=num)

    def with_img_open_procs(self, num: Optional[int]):
        if num is None:
            return self
        return replace(self, img_open_procs=num)

    def with_mod_procs(self, num: Optional[int]):
        if num is None:
            return self
        return replace(self, mod_procs=num)

    def with_hash_procs(self, num: Optional[int]):
        if num is None:
            return self
        return replace(self, hash_procs=num)

    def get_hash_methods_as_name(self) -> tuple[str, ...]:
        methods: list[str] = []
        for method in self.hashing_methods:
            name = HashMethods().to_str(method)
            if name is None:
                continue
            methods.append(name)

        return tuple(methods)

    def get_mods_as_name(self) -> tuple[str, ...]:
        methods: list[str] = []
        for method in self.modifications:
            name = Modifications().to_str(method)
            if name is None:
                continue
            methods.append(name)

        return tuple(methods)


class ConfigInterface:
    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config

    def save_to_json(self, path: Path):
        path.parent.mkdir(exist_ok=True)
        split_path = os.path.splitext(path)[0]
        path = Path(split_path + ".json")
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    def save_to_toml(self, path: Path):
        path.parent.mkdir(exist_ok=True)
        with open(path, "w") as f:
            toml.dump(self.to_dict(), f)

    def to_dict(self) -> dict:
        general = {
            "input_path": str(self.config.input_path),
            "hashing_methods": self.config.get_hash_methods_as_name(),
            "modifications": self.config.get_mods_as_name(),
        }

        procs = {
            "db_fetcher_procs": self.config.db_fetcher_procs,
            "img_open_procs": self.config.img_open_procs,
            "mod_procs": self.config.mod_procs,
            "hash_procs": self.config.hash_procs,
        }

        return {"general": general, "procs": procs}

    @staticmethod
    def default_config_path() -> Path:
        config_file_name = "config.toml"
        config = os.environ.get("P_HASH_CONFIG_PATH")
        if config is not None:
            logging.info("Using P_HASH_CONFIG_PATH to store config file")
            return Path(config) / config_file_name
        home = os.environ.get("HOME")
        if home is not None:
            logging.info("Using HOME/.config to store config file")
            return Path(home) / ".config" / "p-hash-python" / config_file_name

        try:
            logging.info("Using cwd to store config file")
            return Path.cwd() / config_file_name
        except Exception as e:
            raise PathError(e)

    @classmethod
    def create_default(cls, path: Optional[Path] = None, force: bool = False) -> None:
        if not path:
            try:
                path = ConfigInterface.default_config_path()
            except Exception as e:
                raise DefaultConfigPathError(e)

        logging.debug(f"Force: {force}, Path: {path}")

        if path.exists() and not force:
            raise ConfigAlreadyExists()

        cls(BenchmarkConfig()).save_to_json(path)

    @classmethod
    def _from_dict(cls, data: dict) -> "BenchmarkConfig":
        config = BenchmarkConfig()

        general = data.get("general")

        if general is not None:
            input_path = Path(general.get("input_path"))
            hashing_methods = tuple(
                HashMethods().to_obj(o) for o in general.get("hashing_methods")
            )
            modifications = tuple(
                Modifications().to_obj(o) for o in general.get("modifications")
            )

        else:
            input_path = None
            hashing_methods = None
            modifications = None

        procs = data.get("procs")

        if procs is not None:
            db_fetcher_procs = procs.get("db_fetcher_procs")
            img_open_procs = procs.get("img_open_procs")
            mod_procs = procs.get("mod_procs")
            hash_procs = procs.get("hash_procs")

        else:
            db_fetcher_procs = None
            img_open_procs = None
            mod_procs = None
            hash_procs = None

        config = (
            config.with_input_path(input_path)
            .with_hashing_methods(hashing_methods)
            .with_modifications(modifications)
            .with_db_fetcher_procs(db_fetcher_procs)
            .with_img_open_procs(img_open_procs)
            .with_mod_procs(mod_procs)
            .with_hash_procs(hash_procs)
        )

        procs = data.get("procs")
        if procs is None:
            procs = {}

        return config

    @classmethod
    def read_file(cls, path: Optional[Path] = None) -> "BenchmarkConfig":
        if path is None:
            path = DEFAULT_TOML_FILE

        with open(path) as f_in:
            entry = toml.load(f_in)

        config = cls._from_dict(entry)

        return config


class PathError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Path error: {self.error}"


class DefaultConfigPathError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Default config error: {self.error}"


class ConfigAlreadyExists(Exception):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return f"Config already exists"
