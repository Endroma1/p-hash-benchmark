import logging
from lib import BenchmarkBuilder, Config, DbGen
from users import User
from pathlib import Path
from hash_methods import AverageHash
from registries import Modifications, HashMethods
from rich import print
from config import ConfigInterface, DEFAULT_TOML_FILE


TEST_IMG = Path("./gruppen_test_bilder/IMG_0651.jpg")
TEST_IMG_FOLDER = Path.cwd() / Path("./gruppens_test_bilder/")
TEST_SAVE_FOLDER = Path.cwd() / "modifed_imgs"
TEST_HASHING_METHOD = AverageHash


def main():
    args = Config().parse()

    if args.get_methods:
        print(HashMethods())
        print(Modifications())

    if args.generate_config:
        ConfigInterface.create_default()

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

    if args.benchmark:
        logging.debug(f"Using images in dir {TEST_IMG_FOLDER}")
        config = ConfigInterface.read_file().config
        print(config)

        BenchmarkBuilder().use_config(config)


if __name__ == "__main__":
    main()
