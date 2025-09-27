import argparse
from .args_interface import SubCommand

from .args_errors import ArgumentNotGivenToParser
from lib import DbGen


class Db(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.subparser = subparser
        self.parser = subparser.add_parser(
            "db", help="Hashes images in db, given by the image paths for each user"
        )
        self._arguments()
        self._init_subcommands()

    def _arguments(self):
        self.parser.add_argument(
            "-g",
            "--generate",
            action="store_true",
            help="Generates hashes and sends to db",
        )

    def _init_subcommands(self):
        db_subparser = self.parser.add_subparsers(dest="db_command")
        GenerateDb(db_subparser)

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        GenerateDb.parse(args)


class GenerateDb(SubCommand):
    def __init__(self, dbparser: argparse._SubParsersAction) -> None:
        self.parser = dbparser.add_parser("generate", help="Generate hahes for user")
        self._arguments()

    def _arguments(self) -> None:
        self.parser.add_argument("-g", "--gen", help="Generates hashes for user")
        self.parser.add_argument(
            "-m", "--method", type=str, help="Hashing method to use"
        )
        self.parser.add_argument("-u", "-user", help="Generates hashes for user")

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        if not args.db_command.path:
            raise ArgumentNotGivenToParser()

        if args.db.method:
            DbGen(args.db.parse, args.db.method)
