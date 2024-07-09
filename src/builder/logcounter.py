from loguru import logger
import sys

class logcounter:
    def __init__(self):
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
        return self.counts
