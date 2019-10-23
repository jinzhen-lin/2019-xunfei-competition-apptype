# -*- coding: utf-8 -*-
import base64
import os
import sys


# USER_AGENT设置
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36"

# 是否遵从robots.txt的君子协定——不遵从
ROBOTSTXT_OBEY = False

# 两个请求之间的间隔
# 对于API提取的代理类型，为保证可用代理数量保持在一个相对合理的水平，可以把值设置0.03-0.05左右
# 对于隧道代理类型，按隧道的频率限制设
DOWNLOAD_DELAY = 0.05

# 是否启用cookies
COOKIES_ENABLED = True

# Redis设置，会被直接传递给redis.StrictRedis
REDIS_SETTINGS = {"host": "172.16.5.202"}

# 是否异常重试
RETRY_ENABLED = False

# 超时时间
DOWNLOAD_TIMEOUT = 5

# 代理设置
# PROXY_TYPE设为api表示使用的代理类型是从api获取代理服务器
# 设为tunnel表示使用隧道代理
# 设为其他表示不启用代理
PROXY_TYPE = "api"
if PROXY_TYPE == "tunnel":
    PROXY_SERVER = "http://http-dyn.abuyun.com:9020"
    PROXY_USER = b"xxxx"  # 通行证书
    PROXY_PASS = b"xxxx"  # 通行密钥
    def get_proxy_auth(username, password):
        username = username if isinstance(username, bytes) else username.encode()
        password = password if isinstance(password, bytes) else password.encode()
        return b"Basic " + base64.b64encode(username + b":" + password)
    PROXY_AUTH = get_proxy_auth(PROXY_USER, PROXY_PASS)
