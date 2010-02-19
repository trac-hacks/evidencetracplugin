
from genshi.builder import tag

def user_scattered(hist):
    todata = reduce(lambda o, t: ( o[0]+[str( int( (t[0]/25) * 100 ) )], o[1]+[str(int( (t[1]/25) * 100 ))] ) ,  hist, ([], []))
    return tag.img(
        src="http://chart.apis.google.com/chart?cht=s&chs=250&chxr=0,0,25,5|1,0,25,5&chxt=x,y,x,y&chxl=2:||actual|3:||expected|&chd=t:%s|%s" % (",".join(todata[1]), ",".join(todata[0])),
        alt="estemated to actual chart")
