class ArgumentNotGivenToParser(Exception):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "Argument was not given to parser. Check the caller condition"


class ConfigError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Config error: {self.error}"


class DbError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Database error: {self.error}"


class PathError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Path error: {self.error}"
