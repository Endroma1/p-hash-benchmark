from abc import ABC, abstractmethod
import argparse


class SubCommand(ABC):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.subparser = subparser
        self._arguments()

    @abstractmethod
    def _arguments(self) -> None:
        pass

    @staticmethod
    @abstractmethod
    def parse(args: argparse.Namespace) -> None:
        pass
