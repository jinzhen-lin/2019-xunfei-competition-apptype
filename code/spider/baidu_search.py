# -*- coding: utf-8 -*-
import pickle
from urllib.parse import quote

import redis
import scrapy
from lxml.html.clean import Cleaner
from scrapy.selector import Selector

import settings
from spider_util import ApptypeCompetitionSpider

HEADERS = {
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Sec-Fetch-Site": "none",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cookie": "ORIGIN=1; ISSW=1; ISSW=1"
}


class BaiduSearchSpider(ApptypeCompetitionSpider):
    name = "baidu_search"
    allowed_domains = ["baidu.com"]
    url = "https://www.baidu.com/s?wd=%s&ie=utf-8"

    def start_requests(self):
        self.proxy_pool = "proxy_pool:baidu"
        self.r = redis.StrictRedis(**settings.REDIS_SETTINGS)
        self.cleaner = Cleaner(javascript=True, style=True)
        appname_list1 = self.r.smembers("rawdata:appname_list")
        appname_list2 = set(self.r.hkeys("baidu:search_result"))
        appname_list = appname_list1 - appname_list2
        for appname in appname_list:
            appname = appname.decode()
            request = scrapy.Request(
                self.url % quote(appname), meta={"appname": appname},
                callback=self.parse, errback=self.process_error, headers=HEADERS
            )
            yield self.set_request_proxy(request)

    def parse(self, response):
        text = self.cleaner.clean_html(response.text)
        sel = Selector(text=text)
        result_list = sel.css(".c-container")
        appname = response.meta["appname"]
        if not result_list:
            if sel.re("很抱歉，没有找到"):
                self.r.hset("baidu:search_result", appname, "")
                return
            else:
                yield self.handle_retry_request(response.request)

        final_res = []
        for res in result_list:
            title = "".join(x.strip() for x in res.xpath("./h3//text()").extract())
            if title.endswith("百度翻译") or title.endswith("百度图片"):
                continue
            abstract = res.xpath(f"./div[1]//text()")
            abstract = "".join(x.strip() for x in abstract.extract())
            final_res.append([title, abstract])
        self.r.hset("baidu:search_result", appname, pickle.dumps(final_res))
