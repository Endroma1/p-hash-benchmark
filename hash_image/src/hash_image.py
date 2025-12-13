from abc import ABC, abstractmethod
from PIL import Image
import numpy as np
import imagehash

class HashingMethod(ABC):
    @abstractmethod
    def hash_image(self, img:Image.Image)->str:
        pass

class HashingMethods:
    hashing_methods:dict[str, type[HashingMethod]] = {}
    
    @classmethod
    def register(cls, name:str):
        def decorator(mod_cls:type[HashingMethod]):
            cls.hashing_methods.update({name:mod_cls})
            return mod_cls
        return decorator

@HashingMethods.register(name="averagehash")
class AverageHash(HashingMethod):
    def __init__(self, hash_size: int = 8) -> None:
        self.hash_size = hash_size

    def hash_image(self, img: Image.Image) -> str:
        image = img.convert("L")
        image = image.resize((self.hash_size, self.hash_size), Image.Resampling.LANCZOS)


        pixels = np.array(image)

        avg = pixels.mean()

        diff = pixels >= avg

        hash_bits = ''.join(['1' if x else '0' for x in diff.flatten()])
        hash_hex = f'{int(hash_bits, 2):0{self.hash_size*self.hash_size//4}x}'

        return hash_hex

@HashingMethods.register(name="dct-hash")
class DCTHash(HashingMethod):
    def __init__(self, hash_size: int = 8) -> None:
        self.hash_size = hash_size

    def hash_image(self, img: Image.Image) -> str:
        arr = imagehash.phash(img, self.hash_size).hash
        bits = arr.flatten()
        bit_string = ''.join('1' if b else '0' for b in bits)
        hash_len_bits = bits.size
        hash_len_hex = hash_len_bits // 4

        return f'{int(bit_string, 2):0{hash_len_hex}x}'


