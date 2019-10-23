# -*- coding: utf-8 -*-
import argparse
from collections import defaultdict

import numpy as np
import pandas as pd
import torch
from hanziconv import HanziConv
from pytorch_transformers import BertTokenizer, XLNetTokenizer
from scrapy.selector import Selector
from torch.utils.data import TensorDataset
from tqdm.auto import tqdm

from apptype_utils import *


mistaked_apkname_list = [
    "com.baidu.appsearch", "com.sogo.appmall", 
    "com.sogou.androidtool", "com.mobiletool.appstore"
]
mistaked_appname_pattern_list = [
    "百度手机助手\\((.*?)\\)", "搜狗手机助手（(.*?)）", "应用商店（(.*?)）"
]
bert_tokenizer = BertTokenizer.from_pretrained(path_bert_tokenizer)
xlnet_tokenizer = XLNetTokenizer.from_pretrained(path_xlnet_tokenizer)
all_tokenizers = {
    "bert": bert_tokenizer,
    "xlnet": xlnet_tokenizer
}

def generate_tensor_data(text_list, model_type="bert", max_len=512):
    tokenizer = all_tokenizers[model_type]
    cls_token = tokenizer.cls_token
    sep_token = tokenizer.sep_token
    pad_token = tokenizer.pad_token

    pad_on_left = model_type in ["xlnet"]
    cls_token_at_end = model_type in ["xlnet"]
    cls_token_segment_id = 2 if model_type in ["xlnet"] else 0
    sep_token_segment_id = 3 if model_type in ["xlnet"] else 0
    pad_token_segment_id = 4 if model_type in ["xlnet"] else 0

    tokens_list = []
    masks_list = []
    segments_list = []
    for text in tqdm(text_list):
        tokens = tokenizer.tokenize(text)
        if cls_token_at_end:
            tokens = tokens[:(max_len - 2)] + [sep_token, cls_token]
            segment_ids = [0] * (len(tokens) - 2) + [sep_token_segment_id, cls_token_segment_id]
        else:
            tokens = [cls_token] + tokens[:(max_len - 2)] + [sep_token]
            segment_ids = [cls_token_segment_id] + [0] * (len(tokens) - 2) + [sep_token_segment_id]

        tokens_len = len(tokens)
        pad_len = max_len - tokens_len
        if pad_on_left:
            tokens = [pad_token] * pad_len + tokens
            masks = [0] * pad_len + [1] * tokens_len
            segment_ids = [pad_token_segment_id] * pad_len + segment_ids
        else:
            tokens = tokens + [pad_token] * pad_len
            masks = [1] * tokens_len + [0] * pad_len
            segment_ids = segment_ids + [pad_token_segment_id] * pad_len
        tokens = torch.LongTensor(tokenizer.convert_tokens_to_ids(tokens))
        masks = torch.LongTensor(masks)
        segment_ids = torch.LongTensor(segment_ids)

        tokens_list.append(tokens.unsqueeze(0))
        masks_list.append(masks.unsqueeze(0))
        segments_list.append(segment_ids.unsqueeze(0))

    tokens_tensor = torch.cat(tokens_list, 0)
    masks_tensor = torch.cat(masks_list, 0)
    segments_tensor = torch.cat(segments_list, 0)
    return tokens_tensor, masks_tensor, segments_tensor


def generate_chusai_dateset(model_type="bert"):
    chusai_df = pickle_load(path_cache / "chusai_df.pkl")
    chusai_tensors = generate_tensor_data(chusai_df["app_desc"], model_type)
    chusai_label_tensor = torch.LongTensor(chusai_df["apptype_le_id"].values)
    chusai_dataset = TensorDataset(*chusai_tensors, chusai_label_tensor)
    pickle_save(chusai_dataset, path_tensor_dataset / f"{model_type}_chusai_dataset.pkl")


def generate_search_dataset(model_type="bert", search_engine="baidu"):
    df = pickle_load(path_cache / "df.pkl")
    test_df = pickle_load(path_cache / "test_df.pkl")
    search_res1 = pickle_load(path_cache / f"{search_engine}_search_res1.pkl")
    search_res2 = pickle_load(path_cache / f"{search_engine}_search_res2.pkl")

    for i, search_res in enumerate([search_res1, search_res2]):
        search_df = df.merge(search_res, how="left", left_on="new_appname", right_on="appname")
        search_tensors = generate_tensor_data(search_df["search_desc"].fillna(""), model_type)
        search_label_tensor = torch.LongTensor(search_df["apptype_le_id"].values)
        search_dataset = TensorDataset(*search_tensors, search_label_tensor)

        search_test_df = test_df.merge(search_res, how="left", left_on="new_appname", right_on="appname")
        search_test_tensors = generate_tensor_data(search_test_df["search_desc"].fillna(""), model_type)
        search_test_dataset = TensorDataset(*search_test_tensors)

        pickle_save(search_dataset, path_tensor_dataset / f"{model_type}_{search_engine}_dataset{i + 1}.pkl")
        pickle_save(search_test_dataset, path_tensor_dataset / f"{model_type}_{search_engine}_test_dataset{i + 1}.pkl")


def generate_qimai_dataset(model_type="bert"):
    df = pickle_load(path_cache / "df.pkl")
    test_df = pickle_load(path_cache / "test_df.pkl")
    apkname2appdesc = pickle_load(path_cache / "apkname2appdesc.pkl")

    qimai_df = df.merge(apkname2appdesc)
    qimai_tensors = generate_tensor_data(qimai_df["app_desc"], model_type)
    qimai_label_tensor = torch.LongTensor(qimai_df["apptype_le_id"])
    qimai_dataset = TensorDataset(*qimai_tensors, qimai_label_tensor)

    qimai_test_df = test_df.merge(apkname2appdesc)
    qimai_test_tensors = generate_tensor_data(qimai_test_df["app_desc"], model_type)
    qimai_test_dataset = TensorDataset(*qimai_test_tensors)
    qimai_test_id = qimai_test_df["id"].tolist()

    pickle_save(qimai_dataset, path_tensor_dataset / f"{model_type}_qimai_dataset.pkl")
    pickle_save(qimai_test_dataset, path_tensor_dataset / f"{model_type}_qimai_test_dataset.pkl")
    pickle_save(qimai_test_id, path_cache / f"{model_type}_qimai_test_id.pkl")


def generate_qimai_addition_dataset(model_type="bert"):
    test_df = pickle_load(path_cache / "test_df.pkl")
    qimai_test_id = pickle_load(path_cache / f"{model_type}_qimai_test_id.pkl")
    appname2appdesc = pickle_load(path_cache / "appname2appdesc.pkl")
    apkname2appdesc = pickle_load(path_cache / "apkname2appdesc.pkl")

    test_df["appname"] = test_df["new_appname"]
    qimai_test_df = test_df.merge(apkname2appdesc)
    qimai_test_df = qimai_test_df[["appname", "app_desc"]]
    chusai_test_df = pickle_load(path_cache / "chusai_test_df.pkl")
    chusai_test_df = chusai_test_df.loc[~chusai_test_df["appname"].isna(), ["appname", "app_desc"]]

    appname2appdesc = pd.concat([
        appname2appdesc, chusai_test_df, qimai_test_df
    ], axis=0, sort=False)
    appname2appdesc["desc_len"] = appname2appdesc["app_desc"].str.replace("[\x00-\xff”“•]", "").str.len()
    appname2appdesc["appname"] = appname2appdesc["appname"].str.lower().str.replace(" ", "")
    appname2appdesc["appname"] = [HanziConv.toSimplified(x) for x in appname2appdesc["appname"]]
    appname2appdesc = appname2appdesc.sort_values("desc_len").drop_duplicates("appname", keep="last")
    appname2appdesc = appname2appdesc.loc[appname2appdesc["desc_len"] >= 8]

    test_df_new = test_df.copy()
    test_df_new = test_df_new.loc[~test_df["id"].isin(qimai_test_id)]
    test_df_new["appname"] = test_df_new["appname"].str.lower().str.replace(" ", "")
    test_df_new["appname"] = [HanziConv.toSimplified(x) for x in test_df_new["appname"]]
    test_df_new = test_df_new.merge(appname2appdesc)

    qimai_addition_test_id = test_df_new["id"].tolist()
    qimai_addition_test_dataset = generate_tensor_data(test_df_new["app_desc"], model_type)
    qimai_addition_test_dataset = TensorDataset(*qimai_addition_test_dataset)

    pickle_save(qimai_addition_test_id, path_cache / "qimai_addition_test_id.pkl")
    pickle_save(
        qimai_addition_test_dataset, 
        path_tensor_dataset / f"{model_type}_qimai_addition_test_dataset.pkl"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_type", help="要生成哪个模型的数据？", 
        choices=["bert", "xlnet"]
    )
    parser.add_argument(
        "--dataset_type", help="要生成哪部分数据？", 
        choices=["search", "chusai", "qimai", "qimai_addition"]
    )
    parser.add_argument(
        "--search_engine", choices=["baidu", "bing"],
        help="要生成哪个搜索引擎的数据，当dataset_type为search时有效"
    )
    args = parser.parse_args()

    if args.dataset_type == "search":
        generate_search_dataset(args.model_type, args.search_engine)
    elif args.dataset_type == "chusai":
        generate_chusai_dateset(args.model_type)
    elif args.dataset_type == "qimai":
        generate_qimai_dataset(args.model_type)
    elif args.dataset_type == "qimai_addition":
        generate_qimai_addition_dataset(args.model_type)

