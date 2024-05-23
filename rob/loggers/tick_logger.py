import logging
import os
from pathlib import Path

import appdirs

_LOG_FILE = Path(appdirs.user_data_dir()) / "robolson" / "tick" / "LOG.txt"


if not _LOG_FILE.exists():
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _LOG_FILE.touch(exist_ok=True)
    # os.makedirs(_LOG_FILE.parent, exist_ok=True)


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    filename=_LOG_FILE,
    filemode="a",
)


FORMAT = "%(message)s"
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
)

log = logging.getLogger("rich")
log.info("**Hello, World!**")
