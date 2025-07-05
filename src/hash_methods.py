from typing import Optional
from pathlib import Path
from PIL import Image
import numpy as np

from interfaces import HashMethod
from registries import HashMethods


@HashMethods.register
class AverageHash(HashMethod):
    _name = "average_hash"

    def __init__(
        self,
        img_path: Optional[Path] = None,
        img: Optional[Image.Image] = None,
        hash_len: int = 16,
    ) -> None:
        super().__init__(img_path, img, hash_len)

    def hash(self) -> str:
        grayscale = self.img.convert("L")
        resize = grayscale.resize((self.hash_len, self.hash_len))

        np_img = np.array(resize)

        avg = np.mean(np_img)

        result = np.where(np_img > avg, 1, 0)

        flattened = result.flatten()

        to_str = "".join(flattened.astype(str))

        hex_result = hex(int(to_str, 2))[2:]

        return hex_result


@HashMethods.register
class MedianHash(HashMethod):
    _name = "median_hash"

    def __init__(
        self,
        img_path: Optional[Path] = None,
        img: Optional[Image.Image] = None,
        hash_len: int = 16,
    ) -> None:
        super().__init__(img_path, img, hash_len)

    def hash(self) -> str:
        grayscale = self.img.convert("L")
        resize = grayscale.resize((self.hash_len, self.hash_len))

        np_img = np.array(resize)

        avg = np.median(np_img)

        result = np.where(np_img > avg, 1, 0)

        flattened = result.flatten()

        to_str = "".join(flattened.astype(str))

        hex_result = hex(int(to_str, 2))[2:]

        return hex_result
