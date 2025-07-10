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
        self._image = modified_image

    def __eq__(self, value: object, /) -> bool:
        return self._image == value

    @property
    def image(self) -> Image.Image:
        return self._image

    def save(self, save_path: Path) -> Optional[Path]:
        """Saves the image with hash as name. Returns optional path to saved image"""

        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._image.save(save_path)
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
        mods: Optional[list[type[Modification]]] = None,
        save_dir: Path = TMP_FOLDER,
    ) -> None:
        self.img = img
        self.mods = mods
        self.save_dir = save_dir
        self.path: Optional[Path] = None

    def set_img(self, path: Image.Image):
        self.img = path
        return self

    def set_mods(self, mods: list[type[Modification]]):
        self.mods = mods
        return self

    def set_save_dir(self, save_dir: Path):
        self.save_dir = save_dir
        return self

    def run(self) -> list[ModImage]:
        if self.mods is None:
            raise ValueError("No modifications assigned to ModProcessBuilder")

        elif self.mods is not None:
            mod_imgs = []
            for mod in self.mods:
                mod_img = ModImage.new(self.img, mod, self.save_dir)

                assert mod_img is not None

                mod_imgs.append(mod_img)

            return mod_imgs

        else:
            raise ValueError("Configuring ModImageBuilder failed")
