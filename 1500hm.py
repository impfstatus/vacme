from logging.config import fileConfig
import logging
from os import fdopen, fpathconf, system
import requests
import json
import re
import random
import html
import pkce
import time
import sys
import smtplib
import dateutil.parser
import locale
import pathlib
import datetime
import pickle
import vacmebackend
import config
import util
import impfzentrum
import twitter.error
import twitter.api
import twitterclient
import os
import traceback
import vacmelogger

logger = logging.getLogger(__name__)


def main(argv):

    try:

        logger.info('This is a message!')

        tw = twitterclient.tweeter(config.twitterApiKey, config.twitterApiSecret,
                                   config.twitterAccessToken, config.twitterAccessTokenSecret)
        twbe = twitterclient.tweeter(config.twitterApiKey, config.twitterApiSecret,
                                     config.twitterAccessTokenBE, config.twitterAccessTokenSecretBE)

        bernBackend = vacmebackend.vacmeBackend(config.beStartURL, "USERID", "username",
                                                "ImpfMich1", config.proxies, config.verifyCert, config.beDataFile, config.beBackupFile, "Kanton Bern", "#Impfen Bern", config.beHtmlFile, twbe, config.BeRemoteSMS, config.MaxDeltaAdvancedNotificationBE, config.beJsonFile)


        try:
            bernBackend.restoreTokensFromFile(
                json.loads(util.load(config.beBackupFile)))
            bernBackend.impfZentren = pickle.loads(
                util.loadb(config.beDataFile))
        except:
            logger.error(
                "Unexpected error while restoring configuration: %s", sys.exc_info())

        zhBackend = vacmebackend.vacmeBackend(config.zhStartURL, "USERID2", "username2",
                                              "ImpfMich1", config.proxies, config.verifyCert, config.zhDataFile, config.zhBackupFile, "Kanton Zürich", "#Impfen Zürich #züriimpft", config.zhHtmlFile, tw, config.ZhRemoteSMS, config.MaxDeltaAdvancedNotification, config.zhJsonFile)

        try:
            zhBackend.restoreTokensFromFile(
                json.loads(util.load(config.zhBackupFile)))
            zhBackend.impfZentren = pickle.loads(
                util.loadb(config.zhDataFile))
        except:
            print("Unexpected error while restoring configuration: %s", sys.exc_info())

        while True:
            try:
                # os.system('clear')

                for backend in (bernBackend, zhBackend):
                    backend.updateListe()

                    logger.debug(backend.getStatus())
                    backend.conditionalTweet()

                    backend.saveData()
                    backend.saveHTML()
                    backend.saveJson()

            except:
                logger.warning("Unexpected error while updating: %s",
                            sys.exc_info())
                traceback.print_exc()
            finally:
                logger.info("going for a nap")
                time.sleep(config.sleepTime)
                logger.info("just woke up")
    except:
        logger.warn("Unexpected error in main loop: %s", sys.exc_info())
        traceback.print_exc()
    finally:
        logger.info("going for a nap")
        time.sleep(config.sleepTime)
        logger.info("just woke up")


if __name__ == "__main__":
    main(sys.argv)
