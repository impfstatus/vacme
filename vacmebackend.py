import requests
import re
import json
import util
import html
import time
import macros
import sys
import dateutil
import pkce
import impfzentrum
import pickle
import logging
import mailclient
import twitterclient
from logging.config import fileConfig
import config
import subprocess
import vacmelogger


logger = logging.getLogger(__name__)


class vacmeBackend:
    def __init__(self, startUrl, user, username, password, proxies, verify, izfilepath, tokensfilepath, kanton, werbung, htmlfile, tweeter, remoteSMS, MaxDeltaAdvancedNotification, jsonFile):
        self.startUrl = startUrl
        self.user = user
        self.username = username
        self.password = password
        self.initialReg = startUrl+"/api/v1/public/keycloakconfig/vacme-initialreg"
        self.userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36 Edg/90.0.818.62"
        self.accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        self.userUrl = startUrl+"/overview/"+user
        self.statusUrl = startUrl+"/api/v1/reg/dossier/odi/all/"+user
        self.configUrl = startUrl+"/auth/realms/vacme/.well-known/openid-configuration"
        #post to POST /api/v1/reg/auth/ensureUse (expext 200 0)
        self.ensureUserUrl = startUrl+"/api/v1/reg/auth/ensureUser"
        self.refreshXSRFTokenUrl = startUrl+"/api/v1/reg/auth/refreshXSRFToken"
        self.s = requests.Session()
        self.s.verify = verify
        self.s.max_redirects = 10
        if not proxies is None:
            self.s.proxies = proxies
        self.s.headers['User-Agent'] = self.userAgent
        self.s.headers['Accept'] = self.accept
        r = self.s.get(startUrl, timeout=10)
        # get initial reg /api/v1/public/keycloakconfig/vacme-initialreg
        r = self.s.get(self.initialReg, timeout=10)
        self.settings = json.loads(r.text)
        self.realm = self.settings['realm']
        r = self.s.get(self.configUrl, timeout=10)
        self.config = json.loads(r.text)
        self.auth_server_url = self.settings['auth-server-url']
        self.resource = self.settings['resource']
        self.step1 = self.auth_server_url+"realms/"+self.realm + \
            "/protocol/openid-connect/3p-cookies/step1.html"
        self.step2 = self.auth_server_url+"realms/"+self.realm + \
            "/protocol/openid-connect/3p-cookies/step2.html"
        self.tokenAuthUrl = self.config['token_endpoint']
        self.authorizationEndpoint = self.config['authorization_endpoint']
        self.impfZentren = {}
        self.AuthTokenLifetime = 300
        self.RefreshTokenLifetime = 1800
        self.tokenCT = 0
        self.tokens = None
        self.izFilePath = izfilepath
        self.tokensFilePath = tokensfilepath
        self.kanton = kanton
        self.werbung = werbung
        self.htmlFile = htmlfile
        self.tweeter = tweeter
        self.remoteSMS = remoteSMS
        self.backoffTime = config.initialBackoffTime
        self.MaxDeltaAdvancedNotification = MaxDeltaAdvancedNotification
        self.jsonFile = jsonFile

    def setproxyies(self, proxies):
        self.s.proxies = proxies

    def register(self):
        r = self.s.get(self.step1, timeout=10)

        m = re.findall(""".+document\.cookie = "(.+)\"""",
                       r.text, re.MULTILINE)

        addcookies = {}

        for cookie in m:
            name = cookie.split('=')[0]
            value = cookie.split('=')[1].split(';')[0]
            addcookies[name] = value

        r = self.s.get(self.step2, cookies=addcookies, timeout=10)

        #  state = "b2d0b620-793a-4221-93da-892347cf8b85"
        state = util.randString()

        #  nonce = "ba902eba-6458-4918-8e2a-08ed9726df82"

        nonce = util.randString()

        # rfc7636_challenge    / verifier

        code_verifier, code_challenge = pkce.generate_pkce_pair()

        initialAuthUrl = self.authorizationEndpoint+"?client_id="\
            + self.resource+"&redirect_uri="+self.startUrl+"/start"+"&state="+state +\
            "response_mode=fragment&response_type=code&scope=openid&nonce="+nonce + \
            "&code_challenge="+code_challenge+"&code_challenge_method=S256"

        r = self.s.get(initialAuthUrl, timeout=10)

        return r, code_verifier, code_challenge

    def login(self):

        try:
            r, code_verifier, code_challenge = self.register()

            m = re.search(
                """action="(https://[^\"]+)" method="post">""", r.text)
            postUrl = html.unescape(m.group(1))

            postdata = {"username": self.username, "password": self.password}

            r = self.s.post(postUrl, postdata, timeout=10)

            m = re.search(
                """action="(https://[^\"]+)" method="post">""", r.text)

            if m == None or r.status_code != 200:
                raise Exception('login with username and password failed')

            postUrl = html.unescape(m.group(1))

            if self.remoteSMS:
                logger.info(
                    "getting SMS Data, waiting for %d seconds", config.waitForSMS)
                time.sleep(config.waitForSMS)
                totp = subprocess.run(["ssh", "-i", "~/.ssh/sms_key.pem", "lasts@mausi.ddns.net",
                                      "-p", "3856"], stdout=subprocess.PIPE).stdout.decode().split(" ")[-1:]
            else:
                totp = input('enter sms code:')

            logger.info("using sms code %s", totp)
            postdata = {"smsCode": totp}

            r = self.s.post(postUrl, postdata, timeout=10)

            logger.debug(r.text)

            # code vom link fragment holen

            newLocation = r.url

            m = re.search("""&code=(.*)""", newLocation)

            if m == None:
                raise Exception('login with sms code failed')

            code = m.group(1)

            # post auf POST /auth/realms/vacme/protocol/openid-connect/token
            # mit parameter code, client_id,redirect_uri=homepage des users,code_verifier

            postdata = {"code": code, "client_id": self.resource, "redirect_uri": self.startUrl +
                        "/start", "code_verifier": code_verifier, "grant_type": "authorization_code"}

            r = self.s.post(self.tokenAuthUrl, postdata, timeout=10)

            if (r.status_code != 200):
                raise Exception('login with code failed')

            self.tokens = json.loads(r.text)

            # access tokens lesen

            # cookies setzten

            self.s.headers['Authorization'] = "Bearer " + \
                self.tokens['access_token']

            self.tokenCT = int(time.time())

            self.saveTokens()

            #r = self.s.post(self.ensureUserUrl)

            logger.debug(r.text)

            #https://be.vacme.ch/api/v1/reg/auth/refreshXSRFToken ( get new cookie XSRF-TOKEN)

            #r = self.s.get(self.refreshXSRFTokenUrl)

            self.saveTokens()

            self.backoffTime = config.initialBackoffTime

            logger.info("%s: sms Login OK", self.kanton)

            if self.remoteSMS:
                logger.info("extra waittime after sms login: %d",
                            config.waitForSMS)
                time.sleep(config.waitForSMS)
                logger.info("extra waittime after sms login: --done")

        except:
            logger.warning(
                "Unexpected error while using sms response: %s", sys.exc_info())
            time.sleep(self.backoffTime)
            self.backoffTime = self.backoffTime*2
            logger.warning("backoff time is %d now", self.backoffTime)
            return

    def setTokens(self, tokens):
        self.tokens = tokens
        self.tokenCT = int(time.time())
        self.s.headers['Authorization'] = "Bearer "+self.tokens['access_token']

    def restoreTokensFromFile(self, tokens):
        self.tokens = tokens
        self.tokenCT = 0
        self.s.headers['Authorization'] = "Bearer "+self.tokens['access_token']

    def saveTokens(self):
        util.save(json.dumps(self.tokens), self.tokensFilePath)

    def saveData(self):
        util.savebin(pickle.dumps(self.impfZentren), self.izFilePath)

    def refreshTokens(self, force):

        logger.debug('%s: entering refresh tokens', self.kanton)

        if (((int(time.time())-self.tokenCT > 0.8*self.AuthTokenLifetime) or force)):

            logger.info('%s: starting to refresh tokens', self.kanton)

            r, code_verifier, code_challenge = self.register()

            logger.debug(r.text)

            state = util.randString()

            #  nonce = "ba902eba-6458-4918-8e2a-08ed9726df82"

            nonce = util.randString()

            if (r.status_code == 200 and self.tokens is not None):

                postdata = {"client_id": self.resource, "redirect_uri": self.statusUrl,
                            "code_verifier": code_verifier, "grant_type": "refresh_token", "refresh_token": self.tokens['refresh_token']}

                r = self.s.post(self.tokenAuthUrl, postdata, timeout=10)

                if r.status_code == 200:
                    self.tokens = json.loads(r.text)

                    logger.debug(r.text)

                    # access tokens lesen

                    # cookies setzten

                    self.tokenCT = int(time.time())
                    self.s.headers['Authorization'] = "Bearer " + \
                        self.tokens['access_token']

                    self.saveTokens()

                    logger.info('tokens refreshed')

                    #r = self.s.post(self.ensureUserUrl)

                    #r = self.s.get(self.refreshXSRFTokenUrl)

                    #self.saveTokens()

                    # print(r.text)
                else:
                    logger.warn("lost session, starting login")

                    # self.tweeter.tweet("ls")

                    self.login()
            else:
                logger.warn("lost session, starting login")
                self.login()

    def nextfree(self, iz_id):

        logger.debug('entering nextfree')

        checkUrl = self.startUrl+"/api/v1/reg/dossier/termine/nextfrei/"+iz_id+"/ERSTE_IMPFUNG"
        self.refreshTokens(False)
        r = self.s.post(checkUrl, headers={
                        'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=10)

        if (r.status_code == 200 and len(r.text) > 2):

            erstertermin = r.text
            datum = json.loads(r.text)
            datum = dateutil.parser.parse(str(datum['nextDate']))

            postdata = r.text

            checkUrl = self.startUrl+"/api/v1/reg/dossier/termine/frei/" + \
                iz_id+"/ERSTE_IMPFUNG"

            r = self.s.post(checkUrl, postdata, headers={
                            'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=10)

            logger.debug(r.text)

            if (r.status_code == 200 and len(r.text) > 2):

                fstatus = json.loads(r.text)

                kapazitaetErsteImpfung = 0

                for x in fstatus:
                    kapazitaetErsteImpfung = kapazitaetErsteImpfung + \
                        x['kapazitaetErsteImpfung']

                self.refreshTokens(False)

                postdata = erstertermin

                checkUrl = self.startUrl+"/api/v1/reg/dossier/termine/nextfrei/"+iz_id+"/ZWEITE_IMPFUNG"

                r = self.s.post(checkUrl, postdata, headers={
                                'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=10)

                if (r.status_code == 200 and len(r.text) > 2):

                    zweitertermin = r.text

                    postdata = zweitertermin

                    checkUrl = self.startUrl+"/api/v1/reg/dossier/termine/frei/"+iz_id+"/ZWEITE_IMPFUNG"

                    r = self.s.post(checkUrl, postdata, headers={
                        'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=10)

                    if (r.status_code == 200 and len(r.text) > 2):

                        fstatus = json.loads(r.text)

                        kapazitaetZweiteImpfung = 0

                        for x in fstatus:
                            kapazitaetZweiteImpfung = kapazitaetZweiteImpfung + \
                                x['kapazitaetZweiteImpfung']

                        return datum, kapazitaetErsteImpfung, kapazitaetZweiteImpfung
                    else:
                        return macros.MinTime, 0, 0
                else:
                    return macros.MinTime, 0, 0

            else:
                return macros.MinTime, 0, 0
        else:
            return macros.MinTime, 0, 0

    def updateListe(self):

        logger.debug('entering updateListe')

        try:
            self.refreshTokens(False)

            r = self.s.get(self.statusUrl, headers={
                           'Accept': 'application/json'}, timeout=10)

            logger.info(r.status_code)

            if (r.status_code == 200):

                status = json.loads(r.text)

                for x in status:
                    name = x['name']
                    iz_id = x['id']
                    if not iz_id in self.impfZentren:
                        self.impfZentren[iz_id] = impfzentrum.ImpfZentrum(
                            name, iz_id, self.werbung)
                    if (x["terminverwaltung"] and not x["mobilerOrtDerImpfung"] and not x["noFreieTermine"]):
                        date, capacity, capacity2 = self.nextfree(iz_id)
                        self.impfZentren[iz_id].setNextAvailableDay(
                            date, capacity, capacity2)
                    else:
                        self.impfZentren[iz_id].setNextAvailableDay(
                            macros.MinTime, 0, 0)
        except:
            logger.error("Unexpected error: %s", sys.exc_info())
            raise
        self._sortListe()

        logger.info(self.kanton+": got " +
                    str(len(self.impfZentren))+" entries now")

    def _sortListe(self):

        self.impfZentren = dict(
            sorted(self.impfZentren.items(), key=lambda item: item[1].nextAvailableDay, reverse=True))

    def getStatus(self):

        retval = ""

        for x in self.impfZentren:
            iz = self.impfZentren[x]
            nextavail, capacity, capacity2, lastUpdate, lastChange = iz.getNextAvailableDay()
            lastUpdateString = lastUpdate.strftime(
                "%A, %d. %B %Y um %H Uhr %M %S Sekunden")
            nextavailString = nextavail.strftime("%A, %d. %B %Y")
            #if not nextavail == 'Donnerstag, 01. Januar 1970':
            retval = retval + iz.name.replace("_", "")+": "+str(capacity) + " "+str(capacity2) + \
                " Termine ab " + nextavailString + ", letzter Update: "+lastUpdateString+"\n"
        return retval

    def getHTML(self):
        retval = "<html><body><table style=\"width:100%\"><tr><th>Name</th><th>1. freier Termin</th><th>Anzahl</th><th>1. freies Datum</th><th><letztes Update></th></tr>"

        mylist = dict(sorted(self.impfZentren.copy().items(),
                             key=lambda item: item[1].nextAvailableDay))

        for x in mylist:
            iz = mylist[x]
            izName = iz.name.replace("_", "")
            nextavail, capacity, capacity2, lastUpdate, lastChange = iz.getNextAvailableDay()
            lastUpdateString = lastUpdate.strftime("%A, %d. %B %Y um %H Uhr %M %S Sekunden")
            nextavailString = nextavail.strftime("%A, %d. %B %Y")

            if not nextavail == macros.MinTime:
                retval = retval+"<tr><td>"+izName+"</td><td>"+nextavailString + \
                    "</td><td>"+str(capacity)+"</td><td>" + \
                    lastUpdateString+"</td></tr>"
        retval = retval+"</table></body></html>"
        return retval

    def saveHTML(self):
        html = self.getHTML()
        util.save(html, self.htmlFile)
        return

    def getJson(self):
        data = []
        mylist = dict(sorted(self.impfZentren.copy().items(),
                             key=lambda item: item[1].nextAvailableDay))

        for x in mylist:
            iz = mylist[x]
            izName = iz.name.replace("_", "")
            nextavail, capacity, capacity2, lastUpdate, lastChange = iz.getNextAvailableDay()


            data.append({
                'name': izName,
                'nextavail': nextavail.isoformat(),
                'capacity': capacity,
                'capacity2': capacity2,
                'lastUpdate': lastUpdate.isoformat(),
                'lastChange': lastChange.isoformat()}
            )

        return json.dumps(data)


    def saveJson(self):
        json = self.getJson()
        util.save(json, self.jsonFile)

    def conditionalTweet(self):
        logger.info("called conditional Tweet")
        for iz in self.impfZentren:
            self.impfZentren[iz].conditionalTweet(
                self.startUrl, self.tweeter, self.werbung, self.MaxDeltaAdvancedNotification)
