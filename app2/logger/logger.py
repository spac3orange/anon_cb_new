from loguru import logger

logger.add("app/logs/main_log.log", rotation="100 MB", encoding='utf-8', level="INFO")
logger.add("app/logs/errors.log", rotation="100 MB", encoding='utf-8', level="ERROR")
logger.add("app/logs/warnings.log", rotation="100 MB", encoding='utf-8', level="ERROR")