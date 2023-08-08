import requests
import locale
import datetime
import logging


zhBackupFile = "zhBackend.save"
beBackupFile = "beBackend.save"
zhHtmlFile = "zhHtml.html"
beHtmlFile = "beHtml.html"
zhJsonFile = "zh.json"
beJsonFile = "be.json"

configDir = "vacme/.vacme"
zhDataFile = "zhImpfzentren.save"
beDataFile = "beImpfzentren.save"

beStartURL = "https://be.vacme.ch"

zhStartURL = "https://zh.vacme.ch"

minTweetFreqSec = datetime.timedelta(hours=6)
minCapacityForTweet = 1
MaxDeltaAdvancedNotification = datetime.timedelta(days=5)
MaxDeltaAdvancedNotificationBE = datetime.timedelta(days=5)
MaxSchnaeppchen = datetime.timedelta(days=3)
MaxShortTime = datetime.timedelta(minutes=15)
sehrKurz = datetime.timedelta(minutes=5)
MaxTweetInterestTime = datetime.timedelta(minutes=180)

sleepTime = 15

waitForSMS = 60

initialBackoffTime = 300

BeRemoteSMS = True
ZhRemoteSMS = True

twitterTimeout = 5
twitterTimeoutMax = 900

locale.setlocale(locale.LC_TIME, "de_CH.utf8")

proxies = {
    'http': 'http://172.17.240.1:8080',
    'https': 'http://172.17.240.1:8080'
}

impfargumente = ["schützen Sie sich selber 💪💪💪",
                 "schützen Sie Ihre Familie 🥰😃😃😃",
                 "schützen Sie Ihre Mitmenschen 😍😃😃😃",
                 "10-20% haben länger als 1 Monat Symptome 😩🤒😔",
                 "Kinder schützen die Familie 👩‍❤️‍💋‍👨😃😃😃",
                 "Masern, Pocken aber nicht Covid19? 😉😉😉",
                 "das Impfrisiko ist äusserst klein 👍😃😃",
                 "Spitäler überlasten? 🏥😰😰😰",
                 "Operationen verschieben? 🏥😥😥",
                 "teures Testen statt Impfen? 🤑🤑😃😃😃",
                 "es tut nicht weh 😉😉😉",
                 "mRNA Impfungen seit 20 Jahren 👍👍👍",
                 "Freiheiten im Ausland ✈️🚆🏖️🌴🛕🚀👍",
                 "ungeimpfte überlasten Spitäler 🏥😰😰😰",
                 "opfern Sie eine Stunde 🕐😃😃😃",
                 "es kostet nichts 👍👍👍",
                 "94% der Spanier wollen impfen 😲👍👍👍"]

 
proxies = None

verifyCert = True


twitterApiKey = ""
twitterApiSecret = ""
twitterAccessToken = ""
twitterAccessTokenSecret = ""

twitterAccessTokenBE = ""
twitterAccessTokenSecretBE = ""


