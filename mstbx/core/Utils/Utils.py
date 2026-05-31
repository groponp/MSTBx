import logging
import os
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class MSTBxLogger:
    @staticmethod
    def setup_logger(name="MSTBx"):
        logger = logging.getLogger(name)
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            
            # Format: [LEVEL HH:MM:SS DD/MM/YYYY] Message
            formatter = logging.Formatter(
                fmt='[' + Fore.YELLOW + '%(levelname)s' + Fore.RESET + ' ' + Fore.CYAN + '%(asctime)s' + Fore.RESET + '] %(message)s',
                datefmt='%H:%M:%S %%d/%%m/%%Y'
            )
            
            # File Handler (no colors)
            file_formatter = logging.Formatter(
                fmt='[%(levelname)s %(asctime)s] %(message)s',
                datefmt='%H:%M:%S %d/%m/%Y'
            )
            
            sh = logging.StreamHandler()
            sh.setFormatter(formatter)
            logger.addHandler(sh)
            
            # Optionally log to file
            log_file = os.path.join(os.getcwd(), "mstbx_session.log")
            fh = logging.FileHandler(log_file)
            fh.setFormatter(file_formatter)
            logger.addHandler(fh)
            
        return logger

class UnixMessage:
    """Legacy class updated to use the new Logger system."""
    def __init__(self):
        self.logger = MSTBxLogger.setup_logger()

    def message(self, message, type="info"):
        if type.lower() == "info":
            self.logger.info(message)
        elif type.lower() == "warning":
            self.logger.warning(message)
        elif type.lower() == "error":
            self.logger.error(message)

    def makedir(self, dirs):
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                self.logger.info(f"Directory created: {d}")

    def date(self):
        return datetime.now().strftime("%H:%M:%S %d/%m/%Y")
