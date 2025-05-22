from pyrogram.enums import ParseMode

from config import LOG_GROUP_ID
from AlexaMusic.utils.database import is_on_off
from AlexaMusic import app
import logging
from colorama import init, Fore, Style

init(autoreset=True)

LEVEL_COLORS = {
    "DEBUG": Fore.BLUE,
    "INFO": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED + Style.BRIGHT,
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname_color = LEVEL_COLORS.get(record.levelname, "")
        record.levelname = f"{levelname_color}{record.levelname}{Style.RESET_ALL}"
        record.name = f"{Fore.CYAN}{record.name}{Style.RESET_ALL}"
        record.msg = f"{Fore.WHITE}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

def LOGGER(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    formatter = ColoredFormatter("[%(asctime)s] %(name)s - %(levelname)s - %(message)s", "%H:%M:%S")
    handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger