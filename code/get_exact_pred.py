# -*- coding: utf-8 -*-
import pandas as pd
import torch

from apptype_utils import *
from hanziconv import HanziConv

df = pickle_load(path_cache / "df.pkl")
test_df = pickle_load(path_cache / "test_df.pkl")
df["appname"] = df["new_appname"]
test_df["appname"] = test_df["new_appname"]
chusai_df = pickle_load(path_cache / "chusai_df.pkl")
chusai_df = chusai_df.loc[~chusai_df["appname"].isna()]

appname_exact_apptype = pd.concat([
    chusai_df[["appname", "apptype_le_id"]], 
    df[["appname", "apptype_le_id"]]
], axis=0)
appname_exact_apptype["num"] = 1
appname_exact_apptype = appname_exact_apptype.groupby(["appname", "apptype_le_id"]).count().reset_index()
appname_exact_apptype = appname_exact_apptype.sort_values("num").drop_duplicates("appname", keep="last")
appname_exact_apptype["appname"] = appname_exact_apptype["appname"].str.lower()
appname_exact_apptype = appname_exact_apptype.drop_duplicates("appname", keep="last")

test_df["appname"] = test_df["appname"].str.lower().str.replace(" ", "")
test_df["appname"] = [HanziConv.toSimplified(x) for x in test_df["appname"]]
test_df = test_df.merge(appname_exact_apptype, on="appname")

exact_pred_id = test_df["id"].tolist()
exact_pred_apptype_id = test_df["apptype_le_id"].tolist()
exact_pred_prob = torch.zeros(len(exact_pred_apptype_id), 126)
exact_pred_prob.scatter_(1, torch.LongTensor(exact_pred_apptype_id).view(-1, 1), 1)

pickle_save(exact_pred_prob, path_cache / "exact_pred_prob.pkl")
pickle_save(exact_pred_id, path_cache / "exact_pred_id.pkl")

