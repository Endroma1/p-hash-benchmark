import logging
from multiprocessing import parent_process
from lib import BenchmarkBuilder, Config, DbGen
from users import User
from pathlib import Path
from hashing_methods import AverageHash


TEST_IMG = Path("./gruppen_test_bilder/IMG_0651.jpg")
TEST_IMG_FOLDER = Path.cwd() / Path("./gruppens_test_bilder/")
TEST_SAVE_FOLDER = Path.cwd() / "modifed_imgs"
TEST_HASHING_METHOD = AverageHash


def main():
    paths = [p for p in TEST_IMG_FOLDER.rglob("*") if p.is_file()]
    logging.debug(f"Using images in dir {TEST_IMG_FOLDER}")
    BenchmarkBuilder(paths).set_img_openers(2).set_img_hashers(4).set_img_modifiers(
        4
    ).run()
    args = Config().parse()

    if args.create_user is not None:
        if args.file and args.dir is None:  # If no files are specified
            user = User.create_user(args.create_user)
        elif args.file is not None and args.dir is None:  # If a file is specified
            user = User.create_user(args.create_user, args.file)
        elif args.file is None and args.dir is not None:  # If a dir is specified
            user = User.create_user(args.create_user, args.dir.resolve())
        else:
            print("Invalid input")
            return None

        if user is None:
            print("Failed to create user")
            return None

        user.save_to_db()

    if args.gen:
        if args.file is not None:
            logging.info(f"Generating database with file {args.file}")
            DbGen(args.file, AverageHash).dbgen()
        if args.dir is not None:
            logging.info(f"Generating database with dir {args.dir}")
            DbGen(args.dir, TEST_HASHING_METHOD).dbgen()


if __name__ == "__main__":
    main()
