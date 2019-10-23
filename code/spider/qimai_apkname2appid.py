# -*- coding: utf-8 -*-
import json
from urllib.parse import urlencode, urljoin

import redis
import scrapy

import settings
from qimai_encryptor import QimaiEncryptor
from spider_util import ApptypeCompetitionSpider


class QimaiApkname2appidSpider(ApptypeCompetitionSpider):
    name = 'qimai_apkname2appid'
    allowed_domains = ['qimai.cn']
    uri = "/search/checkHasBundleId"
    url = urljoin("https://api.qimai.cn", uri)

    def start_requests(self):
        self.proxy_pool = "proxy_pool:qimai"
        self.r = redis.StrictRedis(**settings.REDIS_SETTINGS)
        qimai_encryptor = QimaiEncryptor(self.uri)
        apkname_list1 = self.r.smembers("rawdata:apkname_list")  # 全部APK包名
        apkname_list2 = set(self.r.hkeys("qimai:apkname2appid"))  # 已经获取ID的包名
        for apkname in apkname_list1 - apkname_list2:
            apkname = apkname.decode()
            params = {
                "search": apkname,
                "analysis": qimai_encryptor(apkname)
            }
            request = scrapy.Request(
                self.url + "?" + urlencode(params), 
                meta=params, dont_filter=True,
                callback=self.parse, errback=self.process_error
            )
            yield self.set_request_proxy(request)

    def parse(self, response):
        json_data = json.loads(response.text)
        apkname = response.meta["search"]
        if json_data["code"] == 10000:
            # 正常返回APPID
            self.r.hset("qimai:apkname2appid", apkname, json_data["app_id"])
        elif json_data["code"] == 10001:
            # 返回不存在该应用的消息
            self.r.hset("qimai:apkname2appid", apkname, -1)
        else:
            yield self.handle_retry_request(response.request)

