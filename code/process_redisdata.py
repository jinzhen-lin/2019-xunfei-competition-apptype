# -*- coding: utf-8 -*-
import pickle
import re
from collections import defaultdict

import pandas as pd
import redis
from scrapy.selector import Selector
from tqdm.auto import tqdm

from apptype_utils import *

r = redis.StrictRedis(**redis_settings)
mistaked_apkname_list = [
    "com.baidu.appsearch", "com.sogo.appmall", 
    "com.sogou.androidtool", "com.mobiletool.appstore"
]
mistaked_appname_pattern_list = [
    "百度手机助手\\((.*?)\\)", "搜狗手机助手（(.*?)）", "应用商店（(.*?)）"
]


appname2appdesc_dict = {}
appname2appdesc_len_dict = defaultdict(int)
apkname2appdesc_dict = {}
apkname2appdesc_len_dict = defaultdict(int)

qimai_appbaseinfo = r.hgetall("qimai:appbaseinfo")
for apkname_market, appinfo in tqdm(qimai_appbaseinfo.items()):
    if not appinfo:
        continue
    apkname, market = apkname_market.decode().split("#")
    appinfo = pickle.loads(appinfo)

    app_desc = Selector(text=appinfo["app_desc"]).xpath("//text()").extract()
    app_desc = "".join(x.strip() for x in app_desc)
    new_app_desc = re.sub("[\x00-\xff”“•]", "", app_desc)
    appname = appinfo["app_name"]

    if not app_desc:
        continue
    if appname2appdesc_len_dict[appname] <= len(new_app_desc):
        appname2appdesc_dict[appname] = app_desc
        appname2appdesc_len_dict[appname] = len(new_app_desc)
    if apkname2appdesc_len_dict[apkname] <= len(new_app_desc):
        apkname2appdesc_dict[apkname] = app_desc
        apkname2appdesc_len_dict[apkname] = len(new_app_desc)

qimai_addition_appbaseinfo = r.hgetall("qimai:addition_appbaseinfo")
for appid_market, appinfo in tqdm(qimai_addition_appbaseinfo.items()):
    if not appinfo:
        continue
    appinfo = pickle.loads(appinfo)

    app_desc = Selector(text=appinfo["app_desc"]).xpath("//text()").extract()
    app_desc = "".join(x.strip() for x in app_desc)
    new_app_desc = re.sub("[\x00-\xff”“•]", "", app_desc)
    appname = appinfo["app_name"]

    if not app_desc:
        continue
    if appname2appdesc_len_dict[appname] <= len(new_app_desc):
        appname2appdesc_dict[appname] = app_desc
        appname2appdesc_len_dict[appname] = len(new_app_desc)

appname2appdesc = pd.DataFrame(pd.Series(appname2appdesc_dict)).reset_index()
appname2appdesc.columns = ["appname", "app_desc"]
appname2appdesc["app_desc"] = appname2appdesc["app_desc"].replace(r"\\\\[rn]", "")
appname2appdesc["app_desc"] = appname2appdesc["app_desc"].replace("[-=*]{2,}", "")
appname2appdesc = appname2appdesc.loc[appname2appdesc["app_desc"] != ""]
pickle_save(appname2appdesc, path_cache / "appname2appdesc.pkl")

for apkname in mistaked_apkname_list:
    if apkname in apkname2appdesc_dict:
        del apkname2appdesc_dict[apkname]
apkname2appdesc = pd.DataFrame(pd.Series(apkname2appdesc_dict)).reset_index()
apkname2appdesc.columns = ["apkname", "app_desc"]
apkname2appdesc["app_desc"] = apkname2appdesc["app_desc"].replace(r"\\\\[rn]", "")
apkname2appdesc["app_desc"] = apkname2appdesc["app_desc"].replace("[-=*]{2,}", "")
apkname2appdesc = apkname2appdesc.loc[apkname2appdesc["app_desc"] != ""]
pickle_save(apkname2appdesc, path_cache / "apkname2appdesc.pkl")

for search_engine in ["bing", "baidu"]:
    search_result = r.hgetall(f"{search_engine}:search_result")
    search_res1 = {}
    search_res2 = {}
    for i, (appname, search_out) in enumerate(tqdm(search_result.items())):
        appname = appname.decode()

        if not search_out:
            search_res1[appname] = ""
            search_res2[appname] = ""
            continue
        search_out = pickle.loads(search_out)

        out_len = len(search_out)
        indices = list(range(out_len))
        random.seed(i)
        random.shuffle(indices)
        part1 = sorted(indices[:round(out_len / 2)])
        part2 = sorted(indices[round(out_len / 2):])
        if part1:
            search_res1[appname] = "。".join("|".join(search_out[i]) for i in part1)
        else:
            search_res1[appname] = ""
        if part2:
            search_res2[appname] = "。".join("|".join(search_out[i]) for i in part2)
        else:
            search_res2[appname] = ""

    search_res1 = pd.DataFrame(pd.Series(search_res1)).reset_index()
    search_res2 = pd.DataFrame(pd.Series(search_res2)).reset_index()
    search_res1.columns = ["appname", "search_desc"]
    search_res2.columns = ["appname", "search_desc"]

    pickle_save(search_res1, path_cache / f"{search_engine}_search_res1.pkl")
    pickle_save(search_res2, path_cache / f"{search_engine}_search_res2.pkl")
