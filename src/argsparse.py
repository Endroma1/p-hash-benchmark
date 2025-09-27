import argparse
from subparsers import (
    args_benchmark,
    args_config,
    args_db,
    args_user,
    args_methods,
)


class Args:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(description="ImageHash Benchmarking Tool")
        subparser = self.parser.add_subparsers(dest="command")
        self.methods = args_methods.Methods(subparser)
        self.user = args_user.User(subparser)
        self.benchmark = args_benchmark.Benchmark(subparser)
        # self.db = args_db.Db(subparser)
        self.config = args_config.Config(subparser)


    def parse(self):
        args = self.parser.parse_args()

        handlers = {
            "config": self.config,
            "methods": self.methods,
            "user": self.user,
            "benchmark": self.benchmark,
            # "db": self.db,
        }

        command = getattr(args, "command", None)

        if command and command in handlers:
            handlers[command].parse(args)
        else:
            self.parser.print_help()
