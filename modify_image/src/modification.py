from abc import ABC, abstractmethod
from PIL import Image
from PIL import ImageEnhance, ImageOps

class Modification(ABC):
    @abstractmethod
    def modify_image(self, img:Image.Image)->Image.Image:
        pass

class Modifications:
    modifications:dict[str,type[Modification]] = {}

    @classmethod
    def register(cls, name:str):
        def decorator(mod_cls:type[Modification]):
            cls.modifications.update({name:mod_cls})
            return mod_cls
        return decorator

@Modifications.register(name="base")
class Base(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return img

@Modifications.register(name="rotate_90")
class Rotate90(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return img.transpose(Image.Transpose.ROTATE_90)

@Modifications.register(name="rotate_180")
class Rotate180(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return img.transpose(Image.Transpose.ROTATE_180)

@Modifications.register(name="flip_left_right")
class FlipLeftRight(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)


@Modifications.register(name="flip_top_bottom")
class FlipTopBottom(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


@Modifications.register(name="grayscale")
class Grayscale(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return ImageOps.grayscale(img)


@Modifications.register(name="invert")
class Invert(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        if img.mode == "RGBA":
            r, g, b, a = img.split()
            rgb = Image.merge("RGB", (r, g, b))
            return Image.merge("RGBA", (*ImageOps.invert(rgb).split(), a))
        return ImageOps.invert(img)

@Modifications.register(name="high_contrast")
class HighContrast(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return ImageEnhance.Contrast(img).enhance(2.0)

@Modifications.register(name="brighten")
class Brighten(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return ImageEnhance.Brightness(img).enhance(1.3)

@Modifications.register(name="sharpen")
class Sharpen(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return ImageEnhance.Sharpness(img).enhance(2.0)
from PIL import ImageFilter

@Modifications.register(name="blur")
class Blur(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return img.filter(ImageFilter.BLUR)


@Modifications.register(name="edge_detect")
class EdgeDetect(Modification):
    def modify_image(self, img: Image.Image) -> Image.Image:
        return img.filter(ImageFilter.FIND_EDGES)

