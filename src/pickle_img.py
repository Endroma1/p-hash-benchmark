import logging
from typing import Optional
from PIL import Image
from pathlib import Path


class PickleableImage:
    def __init__(
        self, raw_data, size: tuple[int, int], mode: str, path: Optional[Path] = None
    ) -> None:
        self.raw_data = raw_data
        self.size = size
        self.mode = mode
        self._path = path

    @property
    def path(self) -> Optional[Path]:
        if self._path is None:
            logging.error("Path not assigned to PickleableImage")
        return self._path

    @classmethod
    def from_pil_image(cls, img: Image.Image, path=None) -> "PickleableImage":
        raw_data = img.tobytes()
        size = img.size
        mode = img.mode

        return cls(raw_data, size, mode, path)

    def to_pil_image(self) -> Image.Image:
        img = Image.frombytes(
            self.mode,
            self.size,
            self.raw_data,
        )
        return img
