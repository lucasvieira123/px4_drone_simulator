from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, override

class Logger(ABC):
    @abstractmethod
    def _write(self, content : str) -> None:
        raise NotImplemented("method not implemented")

    def __with_time_write(self, tag: str, content : Any) -> None:
        return self._write(f'[{tag}] {datetime.now().isoformat()} : {content}')

    def debug(self, content : Any) -> None:
        self.__with_time_write("DEBUG", content)

    def error(self, content : Any) -> None:
        self.__with_time_write("ERROR", content)

    def info(self, content : Any) -> None:
        self.__with_time_write("INFO", content)


class DefaultLogger(Logger):
    @override
    def _write(self, content: str) -> None:
        print(content)

