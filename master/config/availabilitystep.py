import buildbot
from twisted.internet import defer
import requests
from twisted.python import log
import datetime
import email

def parsedate(text):
    return datetime.datetime(*email.utils.parsedate(text)[:6])

class CheckAvailability(buildbot.process.buildstep.BuildStep):

    def __init__(self, url, maxAgeInHours, **kwargs):
        self.url = url
        self.maxAgeInHours = maxAgeInHours
        buildbot.process.buildstep.BuildStep.__init__(self, **kwargs)

    def run(self):
        log.msg("Checking availability of %s" % self.url)
        r = requests.head(self.url)
        log.msg("Request complete")
        log.msg("Status code: %s" % r.status_code)
        if r.status_code != requests.codes.ok:
            log.msg("Request failed: %s" % r.status_code)
            return buildbot.process.results.FAILURE

        log.msg("last modified: %s" % r.headers['last-modified'])
        date = parsedate(r.headers['last-modified'])
        log.msg("parsed: %s" % date)
        if datetime.datetime.now() - datetime.timedelta(hours=self.maxAgeInHours) >= date:
            log.msg("Older than 24h")
            return buildbot.process.results.FAILURE
        return buildbot.process.results.SUCCESS


