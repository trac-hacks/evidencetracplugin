
from genshi.builder import tag

def user_scattered(hist, avg):
    #adding two entries for the velocity line:
    hist += [ (0,0), (15*avg, 15) ]
    est = ",".join(map(lambda t: str( int( (t[0]/25.0) * 100 ) ),  hist))
    act = ",".join(map(lambda t: str( int( (t[1]/25.0) * 100 ) ),  hist))
    return tag.img(
        src="http://chart.apis.google.com/chart?%s&%s&%s&%s&%s&%s&%s" % (
            "cht=s",
            "chs=350x350",
            "chxr=0,0,25,5|1,0,25,5",
            "chxt=x,y,x,y",
            "chxl=2:||expected|3:||actual|",
            "chd=t:%s|%s" % (est, act),
            "chm=o,0000FF,0,-1,6|D,000000,1,-2:,1,-1|o,FF0000,0,0:%d:,5" % len(hist)-3,
            ),
        alt="estemated to actual chart")
