"""
Register all methods for hashing, modification and result calc objects in dictionaries.
"""

from typing import Generic, TypeVar

from rich.console import RenderableType
from rich.text import Text
from interfaces import HashMethod, Modification

T = TypeVar("T")


class Registry(Generic[T]):
    _type: str = ""
    _registry: dict[str, type[T]] = {}

    @classmethod
    def register(cls, method_cls: type[T]) -> type[T]:
        """
        Decorator that registers methods
        """
        name = getattr(method_cls, "_name", None)
        method_name = method_cls.__name__

        if not name:
            raise ValueError(f"Hash method {method_name} must define `name`")

        if name in cls._registry:
            raise ValueError(
                f"Hash method {method_name} already found in registered methods. Is the `name` a duplicate?"
            )

        if not cls._type:
            cls._type = method_cls.__bases__[0].__name__  # Could be bug prone

        cls._registry[name] = method_cls

        return method_cls

    def get_methods(self) -> list[type[T]]:
        return list(self._registry.values())

    def get_names(self) -> list[str]:
        return list(self._registry.keys())

    def __str__(self) -> str:
        if not self._registry:
            return "No hash methods found"

        lines = [f"Registered {self._type}:"]
        for name, obj in self._registry.items():
            lines.append(f" - Name: {name} , Obj-Name: {obj.__name__}")
        return "\n".join(lines)

    def __rich__(self) -> RenderableType:
        text = Text()
        if not self._registry:
            text.append("No hash methods found")
            return text

        text.append(f"Registered {self._type}:\n", style="bold underline")
        for name, obj in self._registry.items():
            text.append(" - ", style="dim")
            text.append("Name: ", style="green")
            text.append(f"{name}", style="bold")
            text.append(" , ", style="dim")
            text.append("Class: ", style="cyan")
            text.append(f"{obj.__name__}\n", style="bold")
        return text


class HashMethods(Registry[HashMethod]):
    _registry: dict[str, type[HashMethod]] = {}


class Modifications(Registry[Modification]):
    _registry: dict[str, type[Modification]] = {}
