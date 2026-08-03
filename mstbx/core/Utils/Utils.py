import logging
import os
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class MSTBxLogger:
    @staticmethod
    def setup_logger(name="MSTBx", log_file=None):
        """Configura el logger compartido de MSTBx.

        Parameters
        ----------
        name : str, default="MSTBx"
            Nombre del logger.
        log_file : str or pathlib.Path, optional
            Archivo de log. Si se omite, usa ``MSTBX_LOG_FILE`` o
            ``mstbx_session.log`` en el directorio de trabajo actual.

        Returns
        -------
        logging.Logger
            Logger configurado con salida de terminal y archivo.
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        target = Path(
            log_file or os.environ.get("MSTBX_LOG_FILE") or (Path.cwd() / "mstbx_session.log")
        ).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            fmt="[" + Fore.YELLOW + "%(levelname)s" + Fore.RESET + " "
            + Fore.CYAN + "%(asctime)s" + Fore.RESET + "] %(message)s",
            datefmt="%H:%M:%S %d/%m/%Y",
        )
        file_formatter = logging.Formatter(
            fmt="[%(levelname)s %(asctime)s] %(message)s",
            datefmt="%H:%M:%S %d/%m/%Y",
        )

        # Rebind handlers on every command. This matters when a process changes
        # directory or when Click/Pytest replaces the captured stderr stream.
        for handler in list(logger.handlers):
            if getattr(handler, "_mstbx_stream", False):
                logger.removeHandler(handler)
                handler.close()
            elif getattr(handler, "_mstbx_file", False):
                current = Path(getattr(handler, "_mstbx_path", "")).resolve()
                if current != target:
                    logger.removeHandler(handler)
                    handler.close()

        if not any(getattr(handler, "_mstbx_stream", False) for handler in logger.handlers):
            stream = logging.StreamHandler()
            stream._mstbx_stream = True
            stream.setFormatter(formatter)
            logger.addHandler(stream)

        if not any(
            getattr(handler, "_mstbx_file", False)
            and Path(getattr(handler, "_mstbx_path", "")).resolve() == target
            for handler in logger.handlers
        ):
            file_handler = logging.FileHandler(target)
            file_handler._mstbx_file = True
            file_handler._mstbx_path = str(target)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        return logger

class UnixMessage:
    """Legacy class updated to use the new Logger system."""
    def __init__(self):
        self.logger = MSTBxLogger.setup_logger()

    def message(self, message, type="info"):
        levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        self.logger.log(levels.get(type.lower(), logging.INFO), message)

    def makedir(self, dirs):
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                self.logger.info(f"Directory created: {d}")

    def date(self):
        return datetime.now().strftime("%H:%M:%S %d/%m/%Y")
