from logging.config import fileConfig
import logging
import sys
import config

fileConfig('logging_config.ini')
logger = logging.getLogger("vacme")

