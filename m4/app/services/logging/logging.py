import logging

# from logstash_async.handler import AsynchronousLogstashHandler
# logger.addHandler(AsynchronousLogstashHandler(host='localhost', port=5959, database_path='logstash.db'))


# def get_logger(level=logging.DEBUG, logger_name="default logger") -> logging.Logger:
def get_logger(logger_name="default logger", level=logging.DEBUG) -> logging.Logger:
    logging.basicConfig(level=level)

    handler = logging.FileHandler("myapp.log")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger
