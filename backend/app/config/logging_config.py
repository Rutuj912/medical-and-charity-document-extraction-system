import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger
from datetime import datetime
from typing import Optional

from .settings import settings


class SafeLogger(logging.Logger):
    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
        **kwargs
    ):

        if kwargs:
            if extra is None:
                extra = {}
            extra.update(kwargs)

        super()._log(
            level,
            msg,
            args,
            exc_info=exc_info,
            extra=extra,
            stack_info=stack_info,
            stacklevel=stacklevel,
        )


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['app'] = settings.APP_NAME
        log_record['environment'] = settings.ENVIRONMENT

        if record.module:
            log_record['module'] = record.module
        if record.funcName:
            log_record['function'] = record.funcName
        if record.lineno:
            log_record['line'] = record.lineno


def get_console_handler() -> logging.StreamHandler:
    console_handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    return console_handler


def get_file_handler(log_file: str = "app.log") -> Optional[TimedRotatingFileHandler]:
    if not settings.LOG_TO_FILE:
        return None

    log_dir = settings.get_absolute_path(settings.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / log_file

    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when=settings.LOG_ROTATION,
        interval=1,
        backupCount=settings.LOG_RETENTION_DAYS,
        encoding='utf-8'
    )

    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    file_handler.setFormatter(formatter)
    return file_handler


def setup_logging(logger_name: Optional[str] = None) -> logging.Logger:

    logging.setLoggerClass(SafeLogger)

    logger = logging.getLogger(logger_name)

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    logger.handlers = []

    console_handler = get_console_handler()
    logger.addHandler(console_handler)

    if settings.LOG_TO_FILE:
        file_handler = get_file_handler()
        if file_handler:
            logger.addHandler(file_handler)

    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    return setup_logging(name)


app_logger = setup_logging("medical_ocr_system")


class LoggerMixin:
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_info(message: str, **kwargs):
    app_logger.info(message, extra=kwargs)


def log_warning(message: str, **kwargs):
    app_logger.warning(message, extra=kwargs)


def log_error(message: str, **kwargs):
    app_logger.error(message, extra=kwargs)


def log_debug(message: str, **kwargs):
    app_logger.debug(message, extra=kwargs)


def log_critical(message: str, **kwargs):
    app_logger.critical(message, extra=kwargs)


if __name__ == "__main__":
    print("Testing Logging Configuration")
    print("=" * 60)

    app_logger.debug("This is a DEBUG message")
    app_logger.info("This is an INFO message")
    app_logger.warning("This is a WARNING message")
    app_logger.error("This is an ERROR message")
    app_logger.critical("This is a CRITICAL message")

    print("\n" + "=" * 60)

    log_info(
        "OCR processing started",
        task_id="task_001",
        file_count=5,
        engine="tesseract"
    )

    log_error(
        "OCR processing failed",
        task_id="task_001",
        error="File not found",
        file_path="/path/to/file.pdf"
    )

    print("\n✓ Logging test completed!")
    print(f"✓ Log file location: {settings.get_absolute_path(settings.LOGS_DIR) / 'app.log'}")
