import argparse
from .args_interface import SubCommand
from .args_errors import ArgumentNotGivenToParser
from registries import HashMethods, Modifications


class Methods(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.subparser = subparser
        self.parser = subparser.add_parser("methods", help="User creation and deletion")
        self._arguments()

    def _arguments(self):
        self.parser.add_argument(
            "-l", "--list", action="store_true", help="Lists all registered methods"
        )

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        if not args.command:
            raise ArgumentNotGivenToParser()

        if args.list:
            print(HashMethods())
            print(Modifications())
            return

        raise ArgumentNotGivenToParser()
