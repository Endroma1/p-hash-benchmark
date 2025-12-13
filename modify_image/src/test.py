import unittest
import tempfile
from PIL import Image
from pathlib import Path
from image import open_image, save_image
from unittest.mock import  MagicMock, patch
from dataclasses import dataclass
import numpy
import modification
import config as cf
import app

class ImageFactory():
    @staticmethod
    def black_image():
        return Image.new("RGB", (100,100), "black")

    @staticmethod
    def random_image():
        data = numpy.random.randint(0, 256, (100,100,3), dtype=numpy.uint8)
        return Image.fromarray(data, "RGB")

class TestOpenImage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".png")
        self.img_path = Path(self.tmp.name)

        self.img:Image.Image = ImageFactory().black_image()
        self.img.save(self.img_path)

    def tearDown(self) -> None:
        self.tmp.close()

    def test_img_bytes(self):
        img:Image.Image = open_image(self.img_path)
        self.assertEqual(img.tobytes(), self.img.tobytes())

    def test_img_size(self):
        img:Image.Image = open_image(self.img_path)
        self.assertEqual(img.size, self.img.size)

    def test_img_mode(self):
        img:Image.Image = open_image(self.img_path)
        self.assertEqual(img.mode, self.img.mode)

class TestSaveImage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(suffix=".png")
        self.img_path = Path(self.tmp.name)

        self.img:Image.Image = ImageFactory.black_image()

    def tearDown(self) -> None:
        self.tmp.close()

    def test_path_exists(self):
        save_image(self.img_path, self.img)

        self.assertTrue(self.img_path.exists())

class TestImageModifications(unittest.TestCase):
    "Tests Modification implementation if modify_image() with whitenoise image"
    def setUp(self) -> None:
        self.img = ImageFactory.random_image()

    def tearDown(self) -> None:
        pass

    def test_base_img(self):
        img = modification.Base().modify_image(self.img)
        self.assertEqual(img, self.img)

class TestConfigFromEnv(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_env(self):
        env_values = {
            "MOD_IMG_PATH": "mod/img/path",
            "INPUT_IMG_PATH": "input/img/path",
            "POSTGRESQL_PORT": "5412",
            "POSTGRESQL_HOST": "posgres.test.io",
            "POSTGRESQL_DB": "test_db",
            "POSTGRESQL_USER": "test_user",
            "POSTGRESQL_PASSWORD": "secret123"
        }

        with patch.dict("os.environ", env_values,  clear=False):
            expected_config = cf.Config.from_env()
            config = cf.Config.from_env()
            self.assertEqual(config, expected_config)

    def test_default(self):
        with patch.dict("os.environ", {}, clear=True):
            expected_config = cf.Config(cf.DEFAULT_MOD_IMG_PATH,
                                        cf.DEFAULT_INPUT_IMG_PATH,
                                        cf.DEFAULT_POSTGRESQL_PORT,
                                        cf.DEFAULT_POSTGRESQL_HOST,
                                        cf.DEFAULT_POSTGRESQL_DB,
                                        cf.DEFAULT_POSTGRESQL_USER,
                                        cf.DEFAULT_POSTGRESQL_PASSWORD)
            config =cf.Config.from_env()

        self.assertEqual(config,  expected_config)

class TestImagePathHash(unittest.TestCase):
    def setUp(self) -> None:
        self.img = ImageFactory.random_image()

    def test_hash_exists(self):
        hash:str = app.hash_image(self.img)
        self.assertGreater(len(hash), 0)

