from abc import ABC


class Logger(ABC):
    def debug(self, content : str) -> None:
        raise NotImplemented("method not implemented")

    def error(self, content : str) -> None:
        raise NotImplemented("method not implemented")

    def log(self, content : str) -> None:
        raise NotImplemented("method not implemented")
