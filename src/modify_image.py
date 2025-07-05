from multiprocessing import Queue
from PIL import Image
from pathlib import Path
from typing import Optional
from crypt_hash import PilSha256
from pickle_img import PickleableImage
from modify_methods import Base
from interfaces import Modification


import logging

TMP_FOLDER = Path.cwd() / "modified_imgs"


class ModImage:
    def __init__(self, modified_image: Image.Image) -> None:
        self.image = modified_image

    def __eq__(self, value: object, /) -> bool:
        return self.image == value

    @property
    def modified_image(self) -> Image.Image:
        return self.image

    def save(self, save_path: Path) -> Optional[Path]:
        """Saves the image with hash as name. Returns optional path to saved image"""

        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.image.save(save_path)
            return save_path
        except Exception as e:
            logging.error(f"Could not save image {save_path}, {e}")
            return None

    @classmethod
    def new(
        cls, img: Image.Image, mod: type[Modification], save_dir: Path = TMP_FOLDER
    ) -> Optional["ModImage"]:
        """Returns the ModifyImage object after saving for later caching"""

        save_path: Path = (
            save_dir / str(mod) / f"{str(PilSha256.crypto_hash(img)) + '.png'}"
        )

        if save_path.exists():
            logging.debug(f"Found image {save_path}")
            return ModImage(Image.open(save_path))

        mod_img = ModImage(mod().modify(img))

        mod_img.save(save_path)

        return mod_img


class ModImageBuilder:
    def __init__(
        self,
        img: Image.Image,
        mod: Optional[type[Modification]] = Base,
        mods: Optional[list[type[Modification]]] = None,
        save_dir: Path = TMP_FOLDER,
        queue: Optional[Queue] = None,
        return_img: bool = True,
        pickle_img: bool = False,
    ) -> None:
        self.img = img
        self.mod = mod
        self.mods = mods
        self.save_dir = save_dir
        self.queue = queue
        self.return_img = return_img
        self.pickleable_img = pickle_img
        self.path: Optional[Path] = None

    def set_img(self, path: Image.Image):
        self.img = path
        return self

    def set_mod(self, mod: type[Modification]):
        self.mod = mod
        return self

    def set_mods(self, mods: list[type[Modification]]):
        self.mods = mods
        return self

    def set_save_dir(self, save_dir: Path):
        self.save_dir = save_dir
        return self

    def set_queue(self, queue: Queue):
        self.queue = queue
        return self

    def set_return_img(self, return_img: bool):
        self.return_img = return_img
        return self

    def set_pickleable_img(self, pickleable: bool, path: Optional[Path] = None):
        self.pickleable_img = pickleable
        self.path = path
        return self

    def run(self) -> list[ModImage] | ModImage | None | Image.Image:
        if self.mod is None and self.mods is None:
            raise ValueError("No modification assigned to ModProcessBuilder")

        if self.mod == self.mods:
            raise ValueError(
                "Cannot take mod and mods parameter at same time in ImageModBuilder"
            )

        if self.mod is not None:
            mod_img = ModImage.new(self.img, self.mod, self.save_dir)
            assert mod_img is not None
            if self.return_img:
                return mod_img.modified_image
            return mod_img

        elif self.mods is not None and self.queue is None:
            mod_imgs = []
            for mod in self.mods:
                mod_img = ModImage.new(self.img, mod, self.save_dir)

                assert mod_img is not None

                if self.return_img:
                    mod_imgs.append(mod_img.modified_image)
                mod_imgs.append(mod_img)

            return mod_imgs

        elif self.mods and self.queue is not None:
            for mod in self.mods:
                mod_img = ModImage.new(self.img, mod, self.save_dir)

                assert mod_img is not None

                img = mod_img.modified_image
                if self.pickleable_img:
                    img = PickleableImage.from_pil_image(img, self.path)
                if self.return_img:
                    self.queue.put(img)
                else:
                    self.queue.put(img)

        else:
            raise ValueError("No mod or mods parameter were given")
