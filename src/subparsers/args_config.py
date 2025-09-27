import argparse
from .args_interface import SubCommand
from .args_errors import ArgumentNotGivenToParser, ConfigError
from config import ConfigInterface


class Config(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.parser = subparser.add_parser("config", help="Config")
        self.subparser = subparser
        self._arguments()

    def _arguments(self):
        self.parser.add_argument(
            "-c",
            "--create",
            action="store_true",
            help="Creates a default template for config",
        )
        self.parser.add_argument("-p", "--path", type=str, help="Path to config")
        self.parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Overwrites config if it already exists",
        )

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        if args.create and args.force:
            try:
                ConfigInterface.create_default(
                    getattr(args.path, "path", None), force=True
                )
            except Exception as e:
                raise ConfigError(e)
            return
        if args.create:
            try:
                ConfigInterface.create_default(getattr(args.path, "path", None))
            except Exception as e:
                raise ConfigError(e)
