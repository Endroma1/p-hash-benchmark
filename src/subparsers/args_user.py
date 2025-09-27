import argparse
from re import sub

from collections import deque
from .args_interface import SubCommand
from pathlib import Path
from .args_errors import ArgumentNotGivenToParser, DbError, PathError
from sqlite_imghash import ImgHashDB
import sqlite3


class User(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.parser = subparser.add_parser("user", help="User creation and deletion")
        self._arguments()
        self._init_subcommands()

    def _arguments(self):
        pass

    def _init_subcommands(self):
        subparser = self.parser.add_subparsers(dest="user_command")
        AddUser(subparser)
        DeleteUser(subparser)
        ModUser(subparser)
        ListUser(subparser)

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        if args.user_command == "add":
            AddUser.parse(args)
        elif args.user_command == "delete":
            DeleteUser.parse(args)
        elif args.user_command == "mod":
            ModUser.parse(args)
        elif args.user_command == "list":
            ListUser.parse(args)


class ListUser(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.parser = subparser.add_parser("list", help="Lists users")
        self._arguments()

    def _arguments(self) -> None:
        self.parser.add_argument("-u", "--user", type=str, help="User to list")
        self.parser.add_argument("--all", action="store_true", help="Lists all users")

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        db = ImgHashDB()

        if args.user:
            try:
                user = db.find_user(args.user)
            except Exception as e:
                raise UserDBError(e)

            print(user)

        if args.all:
            try:
                users = db.find_all_users()
            except Exception as e:
                raise UserDBError(e)

            deque(map(lambda u: print(u), users))


class AddUser(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.parser = subparser.add_parser("add", help="Adds a new user")
        self._arguments()

    def _arguments(self) -> None:
        self.parser.add_argument("username", type=str, help="Username of the new user")
        self.parser.add_argument(
            "-d",
            "--dir",
            type=Path,
            help="Path to image dir that should be linked to user",
        )

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        if not args.user_command:
            raise ArgumentNotGivenToParser()

        if not args.username:
            raise UsernameNotGiven()

        if args.dir:
            try:
                paths = [p for p in args.dir.rglob("*") if p.is_file()]
            except Exception as e:
                raise PathError(e)

            try:
                if args.dir:
                    ImgHashDB().add_user_and_images(args.username, paths).disconnect()

            except Exception as e:
                raise DbError(e)
            return

        try:
            ImgHashDB().add_user(args.username).disconnect()
        except sqlite3.IntegrityError:
            raise UserAlreadyExists(args.username)
        except Exception as e:
            raise DbError(e)


class ModUser(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.parser = subparser.add_parser("mod", help="Modifies a user")
        self._arguments()

    def _arguments(self):
        self.parser.add_argument("username", type=str, help="Username of the user")
        self.parser.add_argument("-p", "--path", type=Path, help="Path to image/images")

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        if not args.username:
            raise UsernameNotGiven()

        if args.path:
            if args.path.is_file():
                try:
                    userdb = ImgHashDB().add_image(args.username, args.path)
                except Exception as e:
                    raise UserDBError(e)
            elif args.path.is_dir():
                paths = [p for p in args.path.rglob("*") if p.is_file()]
                try:
                    userdb = ImgHashDB().add_images(args.username, paths)
                except Exception as e:
                    raise UserDBError(e)

            else:
                raise ModUserParseError("Could not match arguments to input")

            userdb.disconnect()


class ModUserParseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"Failed to parse ModUser argument: {self.message}"


class DeleteUser(SubCommand):
    def __init__(self, subparser: argparse._SubParsersAction) -> None:
        self.parser = subparser.add_parser("delete", help="Deletes a user")
        self._arguments()

    def _arguments(self) -> None:
        self.parser.add_argument("username", type=str, help="Username of the user")

    @staticmethod
    def parse(args: argparse.Namespace) -> None:
        if not args.username:
            raise UsernameNotGiven()

        try:
            ImgHashDB().delete_user(args.username).disconnect()
        except Exception as e:
            raise DbError(e)


class UsernameNotGiven(Exception):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "Username not given for user command"


class UserDBError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Could not find user: {self.error}"


class UserAlreadyExists(Exception):
    def __init__(self, user: str) -> None:
        self.user = user
        super().__init__()

    def __str__(self) -> str:
        return f"User already exists {self.user}"


class NotDirOrFile(
    Exception,
):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()

    def __str__(self) -> str:
        return f"Path is not a dir or a file: {self.path}"
