"""
Interfaces for hashing, modification and result calc objects. For examples, see the associated implementation files.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
from PIL import Image


class Modification(ABC):
    _name: str = ""

    @abstractmethod
    def modify(self, img: Image.Image, **kwargs) -> Image.Image:
        pass

    def __str__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name


class HashMethod(ABC):
    _name: str = ""

    def __init__(
        self,
        img: Image.Image,
        hash_len: int = 16,
    ) -> None:
        if self._name is None:
            raise ValueError(
                "Name for hashing method is not given. Set this in the method constructor"
            )

        self.img = img
        self.hash_len = hash_len

    @abstractmethod
    def hash(self) -> str:
        pass

    def __str__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name
