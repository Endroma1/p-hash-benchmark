from argsparse import Args
from pathlib import Path
from hash_methods import AverageHash
from sqlite_imghash import ImgHashDB 
from subparsers.args_benchmark import ConfigNotFound
from subparsers.args_user import UserAlreadyExists

TEST_IMG = Path("./gruppen_test_bilder/IMG_0651.jpg")
TEST_IMG_FOLDER = Path.cwd() / Path("./gruppens_test_bilder/")
TEST_SAVE_FOLDER = Path.cwd() / "modifed_imgs"
TEST_HASHING_METHOD = AverageHash


def main():
    # Sends hashing and modifying functions to db.
    db = ImgHashDB()
    try: 
        db.send_methods_to_db().disconnect()
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        db.disconnect()

    try:
        Args().parse()
    except UserAlreadyExists as e:
        print(f"User already exists: {e.user}")
    except ConfigNotFound as e:
        print(e)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
