# Some tracer code to see how urlllib and gdal work together

from urllib import urlopen

def open(url):
    try:
        urlopen(url)
        print 'Opened %s' % url
    except IOError as (errno, strerror):
        print "I/O error({0}): {1}: {2}".format(errno, strerror, url)

if __name__ == "__main__":
    print 'load url'
    open("../../lulc_samp_cur")
    print 'load gdal'
    