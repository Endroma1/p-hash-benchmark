from abc import ABC, abstractmethod
from PIL import Image
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


