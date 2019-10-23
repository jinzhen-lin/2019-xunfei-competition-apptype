# -*- coding: utf-8 -*-
import json
from urllib.parse import urlencode, urljoin
import pickle
import redis
import scrapy

import settings
from qimai_encryptor import QimaiEncryptor
from spider_util import ApptypeCompetitionSpider

class QimaiAdditionAppBaseinfoSpider(ApptypeCompetitionSpider):
    name = 'qimai_addition_appbaseinfo'
    allowed_domains = ['qimai.cn']
    uri = "/andapp/baseinfo"
    url = urljoin("https://api.qimai.cn", uri)

    def contruct_request(self, appid, market=None):
        params = {
            "appid": appid
        }
        if market is not None:
            params["market"] = market
        meta = params.copy()
        meta["appid"] = appid
        params["analysis"] = self.qimai_encryptor(params)
        request = scrapy.Request(
            self.url + "?" + urlencode(params), meta=meta, 
            callback=self.parse, errback=self.process_error
        )
        return self.set_request_proxy(request)

    def start_requests(self):
        self.proxy_pool = "proxy_pool:qimai"
        self.r = redis.StrictRedis(**settings.REDIS_SETTINGS)
        self.qimai_encryptor = QimaiEncryptor(self.uri)

        markets_tocrawl = self.r.hgetall("qimai:addition_markets_tocrawl")
        addition_appid = self.r.smembers("qimai:addition_appid")

        for appid in addition_appid:
            appid = appid.decode()
            markets = markets_tocrawl.get(appid.encode(), None)
            if markets is None:
                yield self.contruct_request(appid)
            elif markets != b"":
                markets = markets.decode().split("|")
                for market in markets:
                    yield self.contruct_request(appid, market)

    def parse(self, response):
        json_data = json.loads(response.text)
        appid = response.meta["appid"]

        if json_data["code"] == 10999:
            field = f"{appid}#-1"
            self.r.hset("qimai:addition_appbaseinfo", field, "")
            self.r.hset("qimai:addition_markets_tocrawl", appid, "")
            return
        elif json_data["code"] != 10000:
            yield self.handle_retry_request(response.request)
            return

        market_list = [x["marketId"] for x in json_data["marketList"]]
        if not market_list:
            market_list = ["-1"]
        appinfo = json_data["appInfo"]
        market = response.meta.get("market", market_list[0])
        field = f"{appid}#{market}"
        if "app_name" not in appinfo:
            self.r.hset("qimai:addition_appbaseinfo", field, "")
            self.r.hset("qimai:addition_markets_tocrawl", appid, "")
            return
        final_data = {
            "apkname": appinfo["app_bundleid"],
            "market": market,
            "app_desc": appinfo["app_brief"],
            "app_name": appinfo["app_name"],
            "app_url": appinfo["app_url"],
            "app_category": appinfo["app_category"]
        }
        self.r.hset("qimai:addition_appbaseinfo", field, pickle.dumps(final_data))

        old_market_list = self.r.hget("qimai:addition_markets_tocrawl", appid)
        if old_market_list == b"":
            return
        elif old_market_list is None:
            market_list = market_list[1:]
            self.r.hset("qimai:addition_markets_tocrawl", appid, "|".join(market_list))
        else:
            market_list = old_market_list.decode().split("|")
            market_list = [x for x in market_list if int(x) != int(market)]
            self.r.hset("qimai:addition_markets_tocrawl", appid, "|".join(market_list))
        for market in market_list:
            yield self.contruct_request(appid, market)
