import random
import pathlib
import config


def _randBytes(numberOf):
    return random.randbytes(numberOf).hex()


def randString():
    return _randBytes(8)+"-"+_randBytes(4)+"-"+_randBytes(4)+"-"+_randBytes(12)


def save(tosave, filename):
    fp = pathlib.Path.home() / config.configDir / filename
    f = open(fp, "wb")
    f.write(tosave)
    f.close()


def savebin(tosave, filename):
    fp = pathlib.Path.home() / config.configDir / filename
    f = open(fp, "wb")
    f.write(tosave)
    f.close()


def loadb(filename):
    fp = pathlib.Path.home() / config.configDir / filename
    f = open(fp, "rb")
    retval = f.read()
    f.close()
    return retval


def save(tosave, filename):
    fp = pathlib.Path.home() / config.configDir / filename
    f = open(fp, "w")
    f.write(tosave)
    f.close()


def load(filename):
    fp = pathlib.Path.home() / config.configDir / filename
    f = open(fp, "r")
    retval = f.read()
    f.close()
    return retval


