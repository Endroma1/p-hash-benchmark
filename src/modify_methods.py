from registries import Modifications
from interfaces import Modification
from PIL import Image


@Modifications.register
class Flip(Modification):
    _name: str = "flip"

    def __init__(self) -> None:
        super().__init__()

    def modify(self, img: Image.Image, **kwargs) -> Image.Image:
        flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        return flipped


@Modifications.register
class Base(Modification):
    _name: str = "base"

    def __init__(self) -> None:
        super().__init__()

    def modify(self, img: Image.Image, **kwargs) -> Image.Image:
        return img
