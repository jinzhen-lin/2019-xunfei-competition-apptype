# -*- coding: utf-8 -*-
import argparse
import os
import re
import sys

import redis
import requests

currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from apptype_utils import *
from settings import REDIS_SETTINGS


def import_rawdata_part1():
    r = redis.StrictRedis(**REDIS_SETTINGS)
    df = pickle_load(path_cache / "df.pkl")
    test_df = pickle_load(path_cache / "test_df.pkl")
    appname_list = df["appname"].tolist() + test_df["appname"].tolist() + \
        df["new_appname"].dropna().tolist() + test_df["new_appname"].dropna().tolist()
    r.sadd("rawdata:appname_list", *set(appname_list))
    apkname_list = df["apkname"].tolist() + test_df["apkname"].tolist()
    r.sadd("rawdata:apkname_list", *set(apkname_list))


def import_rawdata_part2():
    r = redis.StrictRedis(**REDIS_SETTINGS)
    old_appid = r.hgetall("qimai:apkname2appid")
    old_appid = set(int(x) for x in old_appid.values())
    all_appid = []
    for i in range(4):
        res = requests.get(f"https://www.qimai.cn/sitemap/android_app_base_{i + 1}.xml")
        all_appid += re.findall("baseinfo/appid/(\\d+)", res.text)
    all_appid = set(int(x) for x in all_appid)
    new_appid = all_appid - old_appid
    r.sadd("qimai:addition_appid", *new_appid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "part", help="需要导入第几部分的数据？（见README.md）", 
        type=int, choices=[1, 2]
    )
    args = parser.parse_args()
    if args.part == 1:
        import_rawdata_part1()
    elif args.part == 2:
        import_rawdata_part2()
    else:
        raise ValueError("part应为1或者2")
