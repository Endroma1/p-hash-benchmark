from db import Db
import logging
from pathlib import Path

TEST_JSON = "test"


def test_db():
    entry = {"user": "001", "hashes": ["ekhawf32", "3ers49rd"]}
    db = Db(TEST_JSON)

    if db is None:
        raise Exception("Could not connect to test db")

    db.add(entry, "awyufplnw3")

    db.save()

    del db

    db = Db(TEST_JSON)

    if db is None:
        raise Exception("Could not connect at second connect")

    result = db.get("001")

    db.delete()

    del db

    db = Db(TEST_JSON, False)

    assert db is None

    logging.debug(f"Asserting {result} with {entry.get("001")}")

    assert result == entry.get("001")


def test_user_file():
    userid = "111"
    img_path = Path.cwd() / "test-mod.jpg"

    user = User.create_user(userid, img_path)

    if user is None:
        raise Exception("Failed to creates user")

    user.save_to_db(TEST_JSON)

    del user

    user = User.load_from_db(userid, TEST_JSON)

    if user is None:
        raise Exception("Could not load user")

    imgs = ["test-mod.jpg"]

    assert imgs == user.images


def test_user_dir():
    userid = "112"
    img_path = Path.cwd() / "gruppens_test_bilder"

    user = User.create_user(userid, img_path)

    if user is None:
        raise Exception("Failed to creates user")

    user.save_to_db(TEST_JSON)

    del user

    user = User.load_from_db(userid, TEST_JSON)

    if user is None:
        raise Exception("Could not load user")

    names = list(
        map(lambda p: p.name, filter(lambda p: p.is_file(), img_path.rglob("*")))
    )

    logging.debug(f"Asserting {names} and {user.images}")

    assert names == user.images
