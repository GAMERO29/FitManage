import logging

from domain.ports import LoggerPort


class PythonLogger(LoggerPort):
    def __init__(self):
        self._logger = logging.getLogger("ventas")

    def info(self, message: str) -> None:
        self._logger.info(message)
