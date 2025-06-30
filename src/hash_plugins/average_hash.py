from typing import Optional
import numpy as np
from PIL import Image
from hashing_methods import HashMethod


class AverageHash(HashMethod):
    def hash(self, img: Image.Image, **kwargs) -> str:
        hash_size: Optional[int] = kwargs.get("hash_size")

        if hash_size is None:
            hash_size = 16

        grayscale = img.convert("L")
        resize = grayscale.resize((hash_size, hash_size))

        np_img = np.array(resize)

        avg = np.mean(np_img)

        result = np.where(np_img > avg, 1, 0)

        flattened = result.flatten()

        to_str = "".join(flattened.astype(str))

        hex_result = hex(int(to_str, 2))[2:]

        return hex_result
