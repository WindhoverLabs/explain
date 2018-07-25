from logging import Logger


class NullLogger(Logger):
    """Suppress all logging."""
    def __init__(self):
        pass

    def critical(self, msg, *args, **kwargs):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def exception(self, msg, *args, exc_info=True, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass


class Loggable(object):
    """A mixin class that provides basic logging methods.

    Subclasses that mix this must set logger in the constructor or otherwise
    before calling any of the logging methods or they will go to a NullLogger.
    """

    def __init__(self, logger: Logger = None):
        if logger is None:
            logger = NullLogger()
        self.logger = logger

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)