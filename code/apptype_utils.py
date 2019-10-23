# -*- coding: utf-8 -*-
import pickle
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import TensorDataset


redis_settings = {"host": "172.16.5.202"}

path_project = Path(r"D:\users\linjinzhen\apptype")
path_rawdata = path_project / "rawdata"
path_submission = path_project / "submission"
path_cache = path_project / "cache"
path_model = path_cache / "model"
path_model_output = path_cache / "model_output"
path_tensor_dataset = path_cache / "tensor_dataset"

global_vars = globals().copy()
for key, value in global_vars.items():
    if key.startswith("path_") and isinstance(value, Path):
        value.mkdir(parents=True, exist_ok=True)

path_pretrained_model = path_project / "../pretrained_model/"
path_bert_tokenizer = path_pretrained_model / "chinese_wwm_ext_pytorch/vocab.txt"
path_bert_model = path_pretrained_model / "chinese_wwm_ext_pytorch/"
path_xlnet_tokenizer = path_pretrained_model / "chinese_xlnet_mid_pytorch/spiece.model"
path_xlnet_model = path_pretrained_model / "chinese_xlnet_mid_pytorch"


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def pickle_save(obj, filename):
    with open(filename, "wb") as f:
        pickle.dump(obj, f)


def pickle_load(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def split_dataset(dataset, train_prop=0.7):
    sample_num = len(dataset)
    train_id = np.random.choice(range(sample_num), int(sample_num * train_prop), replace=False).tolist()
    train_id_set = set(train_id)
    eval_id = [x for x in range(sample_num) if x not in train_id_set]
    train_dataset = TensorDataset(*dataset[train_id])
    eval_dataset = TensorDataset(*dataset[eval_id])
    return train_dataset, eval_dataset
