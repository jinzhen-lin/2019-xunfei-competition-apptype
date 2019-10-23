# -*- coding: utf-8 -*-
import pickle
from csv import QUOTE_NONE

import pandas as pd
import redis
from sklearn.preprocessing import LabelEncoder
from tqdm.auto import tqdm

from apptype_utils import *


mistaked_apkname_list = [
    "com.baidu.appsearch", "com.sogo.appmall", 
    "com.sogou.androidtool", "com.mobiletool.appstore"
]
mistaked_appname_pattern_list = [
    "百度手机助手\\((.*?)\\)", "搜狗手机助手（(.*?)）", "应用商店（(.*?)）"
]
params_read_data = {
    "sep": "\t",
    "header": None,
    "quoting": QUOTE_NONE
}
apptype_id_name = pd.read_csv(path_rawdata / "apptype_id_name.txt", **params_read_data)
apptype_id_name.columns = ["apptype_id", "apptype_name"]
apptype_id_name = apptype_id_name.query("apptype_id > 10000")

# 应用类别的编码
le = LabelEncoder()
apptype_id_name["apptype_le_id"] = le.fit_transform(apptype_id_name["apptype_id"])

# 复赛训练集
df = pd.read_csv(path_rawdata / "final_apptype_train.dat", **params_read_data)
df.columns = ["appname", "apkname", "apptype_id"]
df["appname"] = df["appname"].fillna("")
df = df.assign(apptype_id=df["apptype_id"].str.split('|')).explode('apptype_id')
df["apptype_id"] = df["apptype_id"].astype(int)
df["apptype_le_id"] = le.transform(df["apptype_id"])
df["new_appname"] = np.nan
for pattern in mistaked_appname_pattern_list:
    df["new_appname"] = df["new_appname"].fillna(df["appname"].str.extract(pattern)[0])
df["new_appname"] = df["new_appname"].fillna(df["appname"])

# 复赛测试集
test_df = pd.read_csv(path_rawdata / "appname_package.dat", **params_read_data)
test_df.columns = ["id", "appname", "apkname"]
test_df["appname"] = test_df["appname"].fillna("")
test_df["new_appname"] = np.nan
for pattern in mistaked_appname_pattern_list:
    test_df["new_appname"] = test_df["new_appname"].fillna(test_df["appname"].str.extract(pattern)[0])
test_df["new_appname"] = test_df["new_appname"].fillna(test_df["appname"])

# 初赛训练集
chusai_df = pd.read_csv(path_rawdata / "apptype_train.dat", **params_read_data, usecols=[1, 2])
chusai_df.columns = ["apptype_id", "app_desc"]
chusai_df = chusai_df.assign(apptype_id=chusai_df["apptype_id"].str.split('|')).explode('apptype_id')
chusai_df["apptype_id"] = chusai_df["apptype_id"].astype(int)
chusai_df["apptype_le_id"] = le.transform(chusai_df["apptype_id"])
chusai_df["appname"] = chusai_df["app_desc"].str.extract("《(.*?)》")
chusai_app_desc_head = chusai_df["app_desc"].str[:10]
is_useful_desc = (chusai_app_desc_head.str.find("是") > 0) & \
    (chusai_app_desc_head.str.find("这") < 0) & \
    (chusai_app_desc_head.str.find("你") != 0) & \
    (chusai_app_desc_head.str.find("又") != 0) & \
    chusai_df["appname"].isna()
extracted_appname = chusai_app_desc_head.loc[is_useful_desc].str.extract("(.*?)是")[0]
extracted_appname = extracted_appname.str.replace("，|。|#|\"", "")
chusai_df.loc[is_useful_desc, "appname"] = extracted_appname

# 初赛测试集
chusai_test_df = pd.read_csv(path_rawdata / "app_desc.dat", **params_read_data)
chusai_test_df.columns = ["id", "app_desc"]
chusai_test_df["appname"] = chusai_test_df["app_desc"].str.extract("《(.*?)》")
chusai_test_app_desc_head = chusai_test_df["app_desc"].str[:10]
is_useful_test_desc = (chusai_test_app_desc_head.str.find("是") > 0) & \
    (chusai_test_app_desc_head.str.find("这") != 0) & \
    (chusai_test_app_desc_head.str.find("你") != 0) & \
    (chusai_test_app_desc_head.str.find("又") != 0) & \
    chusai_test_df["appname"].isna()
extracted_test_appname = chusai_test_app_desc_head.loc[is_useful_test_desc].str.extract("(.*?)是")[0]
extracted_test_appname = extracted_test_appname.str.replace("，|。|#|\"", "")
chusai_test_df.loc[is_useful_test_desc, "appname"] = extracted_test_appname


# 保存数据
pickle_save(le, path_cache / "apptype_le.pkl")
pickle_save(apptype_id_name, path_cache / "apptype_id_name.pkl")
pickle_save(df, path_cache / "df.pkl")
pickle_save(test_df, path_cache / "test_df.pkl")
pickle_save(chusai_df, path_cache / "chusai_df.pkl")
pickle_save(chusai_test_df, path_cache / "chusai_test_df.pkl")
