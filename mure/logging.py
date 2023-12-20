import sys
from logging import Formatter, StreamHandler, getLogger
from logging import Logger as _Logger

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
LEVELS = {"DEBUG": DEBUG, "INFO": INFO, "WARNING": WARNING, "ERROR": ERROR}


class Logger:
    """Basic logger."""

    def __init__(self, name: str):
        self.name = name

        # return a logger with the specified name, creating it if necessary
        self._logger = getLogger(name)
        self._formatter = Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

        # stream handler to stdout
        self._stream_handler = StreamHandler(sys.stdout)
        self._stream_handler.setFormatter(self._formatter)
        self._logger.addHandler(self._stream_handler)

        # set level of both the logger and the handler to INFO by default
        self.set_level("INFO")

    def set_level(self, level: str | int):
        """Set log level.

        Parameters
        ----------
        level : str | int
            Level to set.
        """
        # translate string to integer
        if isinstance(level, str):
            level = LEVELS[level.upper()]

        # set the logger's level
        self._logger.setLevel(level)

        # and all handlers
        for handler in self._logger.handlers:
            handler.setLevel(level)

    def debug(self, message: str):
        """Debug log message.

        Parameters
        ----------
        message : str
            Message to log.
        """
        if self._logger.isEnabledFor(DEBUG):
            self._logger._log(DEBUG, message, ())

    def info(self, message: str):
        """Info log message.

        Parameters
        ----------
        message : str
            Message to log
        """
        if self._logger.isEnabledFor(INFO):
            self._logger._log(INFO, message, ())

    def warning(self, message: str):
        """Warning log message.

        Parameters
        ----------
        message : str
            Message to log.
        """
        if self._logger.isEnabledFor(WARNING):
            self._logger._log(WARNING, message, ())

    def error(self, message: str | Exception):
        """Error log message.

        Parameters
        ----------
        message : str
            Message to log.
        """
        if self._logger.isEnabledFor(ERROR):
            if isinstance(message, Exception):
                # log stacktrace if message is an exception
                self._logger._log(ERROR, message, (), exc_info=True)
            else:
                self._logger._log(ERROR, message, ())

    @property
    def in_debug_mode(self) -> bool:
        """Checks if the logger's level is DEBUG.

        Returns
        -------
        bool
            True, if logger is in DEBUG mode, False otherwise.
        """
        return self._logger.level == DEBUG

    @property
    def level(self) -> int:
        """Returns the current log level.

        Returns
        -------
        int
            Log level.
        """
        return self._logger.level

    def __repr__(self):
        """Representation of the logger."""
        return f"<Logger: {self.name} ({self.level})>"


def get_logger(name: str) -> _Logger:
    """Get the specified logger object.

    Parameters
    ----------
    name : str
        Name of the module to get the logger for.

    Returns
    -------
    _Logger
        Logger of the specified module.
    """
    return getLogger(name)


def logger_exists(name: str) -> bool:
    """Check if a logger exists for the specified module.

    Parameters
    ----------
    name : str
        Name of the module to check the logger for.

    Returns
    -------
    bool
        True if logger exists, False otherwise.
    """
    return getLogger(name).hasHandlers()


def set_level(name: str, level: int | str):
    """Set log level for the specified logger.

    Parameters
    ----------
    name : str
        Name of the module.
    level : int | str
        Level to set.
    """
    logger = getLogger(name)

    # translate string to integer
    if isinstance(level, str):
        level = LEVELS[level.upper()]

    # set the logger's level
    logger.setLevel(level)

    # and all handlers
    for handler in logger.handlers:
        handler.setLevel(level)
