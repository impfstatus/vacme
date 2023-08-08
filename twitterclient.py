import util
import config
import sys
import twitter.api
import macros
import vacmelogger
import logging
import requests
import time

logger = logging.getLogger(__name__)


class tweeter:

    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret):

        self.twitterTimeout = config.twitterTimeout

        self.api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=access_token_key, access_token_secret=access_token_secret,
                               timeout=5)

    def backoff(self):
        time.sleep(self.twitterTimeout)
        self.twitterTimeout = self.twitterTimeout * 2
        logger.warn(
            'Twitter API: Error, backoff time is %d seconds, now', self.twitterTimeout)

    def tweet(self, toTweet):

        logger.debug("tweet called %s", toTweet.text)

        requestOK = False
        while not requestOK:
            try:
                self.api.PostUpdate(toTweet.text)
                self.twitterTimeout = config.twitterTimeout
                requestOK = True
                logger.info("tweet successful, reset timeout")
                return
            except requests.exceptions.ReadTimeout:
                self.backoff()
                self.twitterTimeout = self.twitterTimeout * 2
                logger.warn(
                    'Twitter API: ReadTimeout, backoff time is %d seconds, now', self.twitterTimeout)

            except twitter.TwitterError as e:
                self.backoff()
                logger.warn('TwitterError %s', e)
                if e.message[0]['code'] == 187:
                    # duplicate
                    toTweet.neverTweetedBefore = False
                    raise Exception("duplicate")
            except:
                self.backoff()  
                logger.error(
                    "Unexpected error while restoring configuration: %s", sys.exc_info())

        if not requestOK:
            raise Exception('twitter API call timeout out')

    def DirectMessage(self, to, Message):
        result = self.api.PostDirectMessage(text=Message, user_id=to)

    def loadTags():
        return

    def addTags():
        return


def main(argv):
    myapi = tweeter()
    dir(myapi)


if __name__ == "__main__":
    main(sys.argv)
