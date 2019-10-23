# -*- coding: utf-8 -*-
import time

import redis
import requests

import settings

url = "https://proxy.horocn.com/api/proxies"
params = {
    "order_id": "xxxx",
    "num": "10",
    "format": "text",
    "line_separator": "unix",
    "can_repeat": "no"
}

expire_time = 100
proxy_pool_list = ["base", "qimai", "baidu", "bing"]
proxy_pool_list = ["proxy_pool:" + x for x in proxy_pool_list]

while True:
    now_time = int(time.time())
    r = redis.StrictRedis(**settings.REDIS_SETTINGS)
    res = requests.get(url, params=params)
    proxies = [x.strip() for x in res.text.strip().split("\n")]
    for proxy in proxies:
        r.hset("proxy_pool_time", proxy, now_time)
    for proxy_pool in proxy_pool_list:
        old_pool_proxies = r.smembers(proxy_pool)
        for proxy in old_pool_proxies:
            add_time = int(r.hget("proxy_pool_time", proxy))
            if now_time - add_time > expire_time:
                r.srem(proxy_pool, proxy)
        for proxy in proxies:
            r.sadd(proxy_pool, proxy)
    time.sleep(10)
