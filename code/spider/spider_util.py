# -*- coding: utf-8 -*-
import redis
import scrapy

import settings


class ApptypeCompetitionSpider(scrapy.Spider):
    custom_settings = settings.__dict__

    def set_request_proxy(self, request):
        if settings.PROXY_TYPE == "tunnel":
            request.meta["proxy"] = settings.PROXY_SERVER
            request.headers["Proxy-Authorization"] = settings.PROXY_AUTH
        elif settings.PROXY_TYPE == "api":
            proxy = self.r.srandmember(self.proxy_pool)
            proxy = "" if proxy is None else "http://" + proxy.decode()
            request.meta["proxy"] = proxy
        return request

    def handle_retry_request(self, request, replace_proxy=True):
        request = request.replace(dont_filter=True)
        request.meta["_retry_times"] = request.meta.get("_retry_times", 0) + 1
        if request.meta["_retry_times"] > 5:
            return
        if settings.PROXY_TYPE == "api":
            if replace_proxy:
                if "proxy" in request.meta:
                    proxy = request.meta["proxy"][7:]
                    self.r.srem(self.proxy_pool, proxy)
                proxy = self.r.srandmember(self.proxy_pool)
                proxy = "" if proxy is None else "http://" + proxy.decode()
                request.meta["proxy"] = proxy
        return request

    def process_error(self, failure):
        yield self.handle_retry_request(failure.request)

    @property
    def proxy_pool(self):
        if hasattr(self, "_proxy_pool"):
            return self._proxy_pool
        else:
            return "proxy_pool:base"
    
    @proxy_pool.setter
    def proxy_pool(self, proxy_pool):
        self._proxy_pool = proxy_pool

    @property
    def r(self):
        if not hasattr(self, "_r"):
            self._r = redis.StrictRedis(**settings.REDIS_SETTINGS)
        return self._r

    @r.setter
    def r(self, r):
        self._r = r
