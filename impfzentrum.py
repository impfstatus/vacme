import datetime

from requests.sessions import should_bypass_proxies
import macros
import config
import twitter.api
import twitter.error
import sys
import re
import random
import vacmelogger
import logging



logger = logging.getLogger((__name__))




class ImpfTweet:
    def __init__(self, text):
        self.text = text
        self.isSchnaeppchen = False
        self.nextAvailableDay = macros.MinTime
        self.tweetDate = macros.MinTime
        
        self.capacity = 0
        self.url = ""

        

class ImpfZentrum:
    def __init__(self, name, iz_id, werbung):
        self.name = name
        self.iz_id = iz_id
        self.nextAvailableDay = macros.MinTime
        self._capacity = 0
        self._capacity2 = 0
        self.lastTweet = ImpfTweet("")
        self.neverTweetedBefore = True
        self.tweetCounter = 0
        self.lastUpdate = macros.MinTime
        self.werbung=werbung
        self.lastChange = macros.MinTime
        self.triggerTweet = False
        self.triggerEndTweet = False

    def setTweeted(self, tweet):
        self.lastTweet = tweet

    def conditionalTweet(self, url, mytweeter, werbung, myMaxDeltaAdvancedNotification):

        logger.debug("called conditionalTweet")

        myTweet = ImpfTweet("")

        now = datetime.datetime.now()


        comment = ""

        impfargument = config.impfargumente[int(random.random()*len(config.impfargumente))]

        zeit = datetime.datetime.now().strftime("%A, den %d. %B %Y um %H Uhr %M")

        verfuegbar = self.nextAvailableDay != macros.MinTime
        kurzfristig = self.nextAvailableDay-now < config.MaxSchnaeppchen
        langfristig = self.nextAvailableDay - now > myMaxDeltaAdvancedNotification

        warSchnaeppchen = self.lastTweet.isSchnaeppchen
        warVerfuegbar = self.lastTweet.nextAvailableDay != macros.MinTime
        warSehrKurzVerfuegbar = abs(self.lastTweet.tweetDate - now) < config.sehrKurz
        laengerNichtVerfuegbar = not warVerfuegbar and self.lastTweet.tweetDate - \
            now > config.MaxShortTime
        tweetLaengerHer = (
            now-self.lastTweet.tweetDate) > config.MaxTweetInterestTime


        kapazitaetMin12 = min(self._capacity, self._capacity2)

        IZName = self.name.replace("_", "")

        if self.triggerEndTweet:
            logger.info("triggerEndTweet for %s",IZName)
            if warSchnaeppchen:
                wegString = " schon wieder "
                if random.random()< .3:
                    wegString = wegString + "reserviert "
                else:
                    wegString = wegString + "weg "
                comment = IZName+": Das #Impfschnäppchen ist am " + \
                    zeit+wegString+self.werbung
        if ((self.triggerTweet or self.neverTweetedBefore) and kapazitaetMin12 >= config.minCapacityForTweet and not langfristig):
            logger.info("triggerTweet for %s",IZName)

            mengenAngabe=""

            comment = IZName + ": Am "+zeit+" hat es gerade "+mengenAngabe +"Impftermine ab " + \
                self.nextAvailableDay.strftime(
                       "%A, den %-d. %B %Y. ") +self.werbung+" Reservation: "+url
            if kurzfristig:
                comment = comment + " #Impfschnäppchen"
                myTweet.isSchnaeppchen = True
                if random.random() > .5:
                    comment = "#Impfschnäppchen von "+now.strftime("%-H Uhr %M")+": 1. Impfung bereits in "+str((self.nextAvailableDay-now).days)+" Tagen. "+IZName+" "+self.werbung+" Jetzt anmelden: " + \
                        url 

        if len(comment) == 0:
            logger.debug(IZName+': do not tweet')
            return

        comment=comment+" "+impfargument

        myTweet.tweetDate = now
        myTweet.capacity = self._capacity
        myTweet.nextAvailableDay = self.nextAvailableDay
        myTweet.text = comment[0:279]
        myTweet.url = url


        logger.info("zu zwitschern: %s", myTweet.text)


        if myTweet.text == self.lastTweet.text:
            logger.warn("duplicate tweet %s",myTweet.text)
            return
        try:
            mytweeter.tweet(myTweet)
            self.lastTweet = myTweet
            self.neverTweetedBefore = False
            logger.info("gezwitschert: %s", myTweet.text)
            self.triggerTweet = False
            self.triggerEndTweet = False
        except:
            logger.error("Unexpected error: %s", sys.exc_info())

    def setNextAvailableDay(self, nextAvailableDay, capacity, capacity2):
        now = datetime.datetime.now()
        if self.nextAvailableDay != nextAvailableDay or self._capacity != capacity or self._capacity2 != capacity2 or self.nextAvailableDay != nextAvailableDay:
            self.lastChange = now
        if self.nextAvailableDay == macros.MinTime and nextAvailableDay != macros.MinTime:
            self.triggerTweet = True
            self.triggerEndTweet = False
        if self.nextAvailableDay > macros.MinTime and nextAvailableDay == macros.MinTime:
            self.triggerEndTweet = True
            self.TriggerTweet = False
        self.nextAvailableDay = nextAvailableDay
        self._capacity = capacity
        self._capacity2 = capacity2
        self.lastUpdate = datetime.datetime.now()

    def getNextAvailableDay(self):
        return self.nextAvailableDay, self._capacity, self._capacity2, self.lastUpdate, self.lastChange
