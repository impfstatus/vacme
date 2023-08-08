import impfzentrum
import sys
import config
import util
import pickle


def main(argv):
    print ("hello world")

    zhImpfZentren = pickle.loads(util.loadb(config.zhDataFile))
    beImpfZentren = pickle.loads(util.loadb(config.beDataFile))

    for izlist in (zhImpfZentren,beImpfZentren):
        for x in izlist:
            iz=izlist[x]
            print('name','id','lastUpdate',)
            print(iz.name,iz.)



if __name__ == "__main__":
    main(sys.argv)
