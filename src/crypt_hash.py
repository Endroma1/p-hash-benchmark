from abc import ABC, abstractmethod
from PIL import Image
import hashlib
from pathlib import Path


class CryptoHash(ABC):
    def __init__(self, hash: str) -> None:
        self.hash = hash

    def __str__(self) -> str:
        return self.hash

    @classmethod
    @abstractmethod
    def crypto_hash(cls, value) -> "CryptoHash":
        pass


class PilSha256(CryptoHash):
    @classmethod
    def crypto_hash(cls, value: Image.Image) -> "PilSha256":
        img = value.convert("RGB")
        data = img.tobytes()
        hash = hashlib.sha256(data).hexdigest()

        return cls(hash)


class PathSha256(CryptoHash):

    @classmethod
    def crypto_hash(cls, value: Path) -> "PathSha256":
        with Image.open(value) as img:
            obj = PilSha256.crypto_hash(img)
            return cls(str(obj))
