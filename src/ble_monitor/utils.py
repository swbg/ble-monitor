import logging
import sys


def ba_to_str(ba: bytearray, sep: str = ":") -> str:
    return sep.join([f"{b:02X}" for b in ba])


def str_to_ba(s: str, sep: str = ":", base: int = 16) -> bytearray:
    return bytearray([int(s_i, base=base) for s_i in s.split(sep)])


class SimpleFilter(logging.Filter):
    def __init__(self, loglevel: int, leq: bool):
        """
        Initialize filter
        :param loglevel: Decision threshold
        :param leq: Whether to let less or equal levels or higher levels pass
        """
        self.loglevel = loglevel
        self.leq = leq

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records
        :param record: Log record
        :return: Whether to let the record pass
        """
        if self.leq:
            return record.levelno <= self.loglevel
        else:
            return record.levelno > self.loglevel


def set_up_logging(loglevel: int, filename: str = None) -> None:
    """
    Set up basic logging
    :param loglevel: Log level
    :param filename: Filename to write logging data to
    :return: None
    """
    handlers = []
    if loglevel <= logging.INFO:
        info_handler = logging.StreamHandler(sys.stdout)
        info_filter = SimpleFilter(logging.INFO, True)
        info_handler.addFilter(info_filter)

        warning_handler = logging.StreamHandler(sys.stderr)
        warning_filter = SimpleFilter(logging.INFO, False)
        warning_handler.addFilter(warning_filter)

        handlers.extend([info_handler, warning_handler])
    else:
        handlers.append(logging.StreamHandler())

    if filename is not None:
        handlers.append(logging.FileHandler(filename))

    logging.basicConfig(
        level=loglevel,
        handlers=handlers,
        format="[{asctime}] {levelname} {name}.{funcName}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    for logger in [
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if not name.startswith("sqlalchemy")
    ]:
        logger.setLevel(loglevel)
