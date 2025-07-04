from hashing_methods import HashMethod


class HashMethods:
    _registry: dict[str, type[HashMethod]] = {}

    @classmethod
    def register(cls, method_cls: type[HashMethod]) -> type[HashMethod]:
        name = getattr(method_cls, "_name", None)
        if not name:
            raise ValueError(f"Hash method {method_cls.__name__} must define `name`")

        if name in cls._registry:
            raise ValueError(
                f"Hash method {method_cls.__name__} already found in registered methods. Is the `name` a duplicate?"
            )

        cls._registry[name] = method_cls

        return method_cls

    def get_methods(self):
        return self._registry
