from dataclasses import dataclass
from multiprocessing import Process, Queue
from typing import Optional
from sqlitedb import DB, DBNotConnected, QueryNotFound
from pathlib import Path
from colorama import Fore, Style, init
import numpy as np

from multiprocess_tools import STOP, StopSignal
from matching import MatchResult


init(autoreset=True)


class DbImage:
    def __init__(
        self,
        image_id: int,
        value: str,
        hash_method_id: int,
    ) -> None:
        pass


class SendImageQueueToDb:
    def __init__(
        self,
        image_queue: Queue[DbImage | StopSignal],
        db_name: str,
        batch_size: int = 500,
        img_senders: int = 1,
    ) -> None:
        self.queue = image_queue
        self.db_name = db_name
        self.batch_size = batch_size
        self.processes = self._processes(img_senders)

        [p.start() for p in self.processes]

    def _processes(self, processes: int):
        return [Process(target=self._worker) for _ in range(processes)]

    def join(self):
        [p.join() for p in self.processes]

    def _worker(self):
        while True:
            db = DB(self.db_name).connect()
            query = """
                    INSERT INTO hashes (hash) 
                    VALUES (?,?,?);
                    """
            for _ in range(self.batch_size):
                value = self.queue.get()
                if isinstance(value, StopSignal):
                    break

        db.disconnect()


class UserPathsQueuer:
    def __init__(self, processes: int, output_queue: Queue, db_name: str) -> None:
        self.db_name = db_name
        self.db = DB(db_name).connect()
        self.processes = processes
        self.output_queue = output_queue
        cur = self.db.get_cursor()
        cur.execute("SELECT COUNT(*) FROM images")
        self.id_count = cur.fetchone()[0]
        print(f"Count: {self.id_count}")
        cur.close()

        self.fetchers = self._processes()
        self.db.disconnect()

    def join(self, stops: int) -> None:
        for p in self.fetchers:
            p.join()

        for _ in range(stops):
            self.output_queue.put(STOP)

    def _processes(self) -> list[Process]:
        args: list[tuple[int, int]] = [(int(n[0]), int(n[1])) for n in self._batch()]
        print(args)
        return [Process(target=self._worker, args=(tuple(arg))) for arg in args]

    def start(self) -> "UserPathsQueuer":
        for p in self.fetchers:
            p.start()

        return self

    def _batch(self) -> np.ndarray:
        base = self.id_count // self.processes
        remainder = self.id_count % self.processes

        batch_sizes = base + (np.arange(self.processes) < remainder).astype(int)
        ends = np.cumsum(batch_sizes)
        starts = np.r_[0, ends[:-1]]
        ranges = np.column_stack((starts, ends))
        return ranges

    def _worker(self, start_id: int, end_id: int) -> None:
        print("Starting workers")
        query = """
        SELECT path 
        FROM images
        WHERE id BETWEEN ? AND ?;
        """
        args = (start_id, end_id)
        db = DB(self.db_name).connect()

        cursor = db.get_cursor()
        print("Executing query")
        cursor.execute(query, args)
        result = cursor.fetchall()
        print(result)

        for path_tuple in result:
            print(f"Fetching images {path_tuple}")
            self.output_queue.put(path_tuple[0])

        db.disconnect()


@dataclass
class User:
    id: int
    name: str
    images: Optional["Images"]

    def __str__(self) -> str:
        return (
            f"{Fore.CYAN}userid{Style.RESET_ALL}: {self.id}\n"
            f"{Fore.GREEN}Username{Style.RESET_ALL}: {self.name}\n"
            f"{Fore.MAGENTA}images{Style.RESET_ALL}:\n    {self.images}"
        )


@dataclass
class Images:
    images: list[Path]
    user_id: int

    def __str__(self) -> str:
        print(self.images)
        return ",\n    ".join(str(path) for path in self.images)


class ImgHashDB:
    def __init__(self, db_path="users.db") -> None:
        self.db_path = db_path
        self.db: Optional[DB] = DB(db_path).connect()
        self._init_tables()

    def disconnect(self):
        if not self.db:
            return

        self.db.disconnect()

    def _init_tables(self):
        if not self.db:
            raise DBNotConnected()

        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
                );

            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                modification_id INTEGER,
                path TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

            CREATE TABLE IF NOT EXISTS modifications (
                id INTEGER PRIMARY KEY,
                image_id INTEGER,
                name TEXT UNIQUE,
                FOREIGN KEY (image_id) REFERENCES images(id) on DELETE CASCADE
                );

            CREATE TABLE IF NOT EXISTS hash_methods (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
                );
                
            CREATE TABLE IF NOT EXISTS hashes (
                id INTEGER PRIMARY KEY,
                image_id INTEGER,
                value TEXT,
                hash_method_id INTEGER,
                FOREIGN KEY (image_id) REFERENCES images(id) on DELETE CASCADE,
                FOREIGN KEY (hash_method_id) REFERENCES hash_methods(id) on DELETE CASCADE
                );

            CREATE TABLE IF NOT EXISTS hamming_distance (
                id INTEGER PRIMARY KEY,
                hash_id_1 INTEGER,
                hash_id_2 INTEGER,
                value TEXT,
                FOREIGN KEY (hash_id_1) REFERENCES hashes(id) ON DELETE SET NULL
                FOREIGN KEY (hash_id_2) REFERENCES hashes(id) ON DELETE SET NULL
                );
            
            """)

        self.db.execute("PRAGMA foreign_keys = ON;")
        self.db.commit()

    def get_user_paths_to_queue(
        self, processes: int, output_queue: Queue
    ) -> UserPathsQueuer:
        """
        Gets all image paths from db and puts it into the output queue with n number of processes
        """
        return UserPathsQueuer(processes, output_queue, self.db_path)

    def add_hashes_from_user(self, username: str):
        """
        Hashes the images given by imagepaths linked to a user.
        """

    def paths_query(
        self, output_queue: Queue, batch_size: int = 1000, processes: int = 1
    ):
        query = """
        SELECT path 
        FROM images;
        """
        if self.db is None:
            raise DBNotConnected()

        cursor = self.db.execute(query)

    def get_image_paths_from_user(self, username: str) -> Optional[list[Path]]:
        if not self.db:
            raise DBNotConnected()

        try:
            result = self.db.fetchall(
                """
                SELECT path 
                FROM images i
                INNER JOIN users u on i.user_id = u.id
                WHERE name = ?
                """,
                (username,),
            )
        except Exception as e:
            raise GetImagePathsFromUserError(username, e)

        images: list[Path] = [Path(p[0]) for p in result]

        return images

    def delete_all_users(self):
        if not self.db:
            raise DBNotConnected()

        self.db.delete_db()

    def add_user(self, username: str) -> "ImgHashDB":
        if not self.db:
            raise DBNotConnected()

        try:
            self.db.execute("INSERT INTO users (name) VALUES (?)", (username,))
        except Exception as e:
            raise AddUserError(e, username)
        self.db.commit()
        return self

    def find_user(self, username: str) -> User:
        if not self.db:
            raise DBNotConnected()

        try:
            result = self.db.fetchone(
                """
                SELECT u.id, u.name, i.path 
                FROM users u
                LEFT JOIN images i ON u.id = i.user_id
                WHERE u.name = ?
                GROUP BY u.id, u.name
                """,
                (username,),
            )
        except QueryNotFound as e:
            raise UserNotFound(username, e)

        user_id, name, images = result

        if images is None:
            return User(user_id, name, None)
        else:
            images_list = images.split(",")
            path_images = map(lambda s: Path(s), images_list)
            return User(user_id, name, Images(list(path_images), name))

    def find_all_users(self) -> list[User]:
        if not self.db:
            raise DBNotConnected()

        try:
            results = self.db.fetchall(
                """
            SELECT u.id, u.name, GROUP_CONCAT(i.path)
            FROM users u
            LEFT JOIN images i ON u.id = i.user_id
            GROUP BY u.id, u.name
            """
            )
        except QueryNotFound as e:
            raise NoUsersInDB(e)

        users = []
        for row in results:
            user_id, name, images = row
            images_list = images.split(",") if images else []
            path_images = [Path(p) for p in images_list]
            users.append(User(user_id, name, Images(path_images, name)))
        return users

    def delete_user(self, username: str) -> "ImgHashDB":
        if not self.db:
            raise DBNotConnected()

        uid = self._get_user_id(username)

        try:
            self.db.execute(
                "DELETE FROM images WHERE user_id = ?",
                (uid,),
            )
        except Exception as e:
            raise DeleteImagesError(e, int(uid))
        try:
            self.db.execute("DELETE FROM users WHERE name = ?", (username,))
        except Exception as e:
            raise DeleteUsersError(e, int(uid))
        self.db.commit()

        return self

    def add_image(self, username: str, image: Path) -> "ImgHashDB":
        if not image.is_file():
            raise NotAFile(image)

        user = self.find_user(username)
        self._insert_into_images(user.id, image)
        return self

    def add_images(self, username: str, images: list[Path]) -> "ImgHashDB":
        if not self.db:
            raise DBNotConnected()

        user = self.find_user(username)
        userid = user.id
        [self._insert_into_images(userid, path) for path in images]
        return self

    def _insert_into_images(self, userid: int, path: Path):
        if not self.db:
            raise DBNotConnected()

        try:
            self.db.execute(
                "INSERT INTO images (user_id, path) VALUES (?, ?)", (userid, path.name)
            )
        except Exception as e:
            ImageAddError(path, e)

    def add_user_and_images(self, username: str, images: list[Path]) -> "ImgHashDB":
        return self.add_user(username).add_images(username, images)

    def _get_user_id(self, username) -> int:
        if not self.db:
            raise DBNotConnected()

        try:
            cur_uid = self.db.fetchone(
                "SELECT id FROM users WHERE name = ?", (username,)
            )
            if cur_uid is None:
                raise UidNotFound(username)
            return int(cur_uid[0])
        except Exception as e:
            raise GetUidError(e, username)

    def add_match_results(self, match_results: list[MatchResult]):
        if not self.db:
            raise DBNotConnected()

        try:
            self.db.execute(
                """
                INSERT INTO hamming_distance (hash_id_1, hash_id_2, value) 
                VALUES (?,?,?);
                """,
                (
                    match_result._input_hash,
                    match_result._db_hash,
                    match_result._hamming_distance,
                ),
            )
        except Exception as e:
            raise AddMatchResultError(e)


class AddMatchResultError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Could not add match result to db: {self.error}"


class GetUidError(Exception):
    def __init__(self, e: Exception, username: str) -> None:
        self.error = e
        self.username = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Could not get uid for user {self.username}, error: {self.error}"


class UserNotFound(Exception):
    def __init__(self, username: str, e: Exception) -> None:
        self.username = username
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Did not find user {self.username}, {self.error}"


class UidNotFound(Exception):
    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(username)

    def __str__(self) -> str:
        return f"Did not find id for user {self.username}"


class NoUsersInDB(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"No users found in db:  {self.error}"


class DeleteUsersError(Exception):
    def __init__(self, e: Exception, uid: int) -> None:
        self.uid = uid
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Failed to delete user with uid {self.uid}, error: {self.error}"


class DeleteImagesError(Exception):
    def __init__(self, e: Exception, uid: int) -> None:
        self.uid = uid
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Failed to delete images for uid {self.uid}, error: {self.error}"


class DbConnClosed(Exception):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "Db is closed. Cannot connect to db"


class AddUserError(Exception):
    def __init__(self, error: Exception, username: str) -> None:
        self.error = error
        self.username = username
        super().__init__()

    def __str__(self) -> str:
        return f"Failed to add user {self.username}, error: {self.error}"


class NotAFile(Exception):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__()

    def __str__(self) -> str:
        return "Not a file: {self.file}"


class GetImagePathsFromUserError(Exception):
    def __init__(self, username: str, error: Exception) -> None:
        self.username = username
        self.error = error
        super().__init__()

    def __str__(self) -> str:
        return f"Could not get images from user {self.username}, error: {self.error}"


class ImageAddError(Exception):
    def __init__(self, path: Path, error: Exception) -> None:
        self.path = path
        self.error = error
        super().__init__()

    def __str__(self) -> str:
        return f"Could not add images from path {self.path}, error: {self.error}"
