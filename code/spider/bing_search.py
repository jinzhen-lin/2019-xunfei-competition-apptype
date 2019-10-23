# -*- coding: utf-8 -*-
import pickle
import random

import redis
import scrapy

import settings
from spider_util import ApptypeCompetitionSpider

HEADERS = {
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}


class BingSearchSpider(ApptypeCompetitionSpider):
    name = "bing_search"
    allowed_domains = ["bing.com"]
    url = "https://cn.bing.com/search?q=%s"

    def start_requests(self):
        self.proxy_pool = "proxy_pool:bing"
        self.r = redis.StrictRedis(**settings.REDIS_SETTINGS)
        appname_list1 = self.r.smembers("rawdata:appname_list")
        appname_list2 = set(self.r.hkeys("bing:search_result"))
        appname_list = list(appname_list1 - appname_list2)
        random.shuffle(appname_list)
        for appname in appname_list:
            appname = appname.decode()
            request = scrapy.Request(
                self.url % quote(appname), meta={"appname": appname, "cookiejar": appname},
                callback=self.parse, errback=self.process_error, headers=HEADERS.copy()
            )
            yield self.set_request_proxy(request)

    def parse(self, response):
        result_list = response.css("li.b_algo")
        appname = response.meta["appname"]
        if not result_list:
            if "Cookie" not in response.request.headers:
                response.request.meta["retry"] = 0
                yield self.handle_retry_request(response.request, False)
            else:
                if "retry" in response.request.meta:
                    if response.request.meta["retry"] >= 20:
                        return
                    response.request.meta["retry"] += 1
                else:
                    response.request.meta["retry"] = 0
                yield self.handle_retry_request(response.request, False)
            return
        final_res = []
        for res in result_list:
            title = "".join(x.strip() for x in res.xpath("./h2//text()").extract())
            abstract = res.xpath(f".//p//text()")
            abstract = "".join(x.strip() for x in abstract.extract())
            final_res.append([title, abstract])
        self.r.hset("bing:search_result", appname, pickle.dumps(final_res))
