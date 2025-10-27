"""Log counter for tracking log levels in FVM"""
class LogCounter:
    """Class to count the number of log messages at each level."""

    def __init__(self):
        """Class constructor"""
        self.counts = {
            "TRACE": 0,
            "DEBUG": 0,
            "INFO": 0,
            "SUCCESS": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0
        }

    def __call__(self, message):
        level = message.record["level"].name
        if level in self.counts:
            self.counts[level] += 1

    def get_counts(self):
        """Returns the current log level counts."""
        return self.counts
