# -*- coding: utf-8 -*-
import os
import re

import pandas as pd
import torch

from apptype_utils import *


qimai_test_res_names = [
    "bert_qimai_test_dataset_epoch5_res",
    "bert_qimai_test_dataset_epoch6_res",
    "xlnet_qimai_test_dataset_epoch5_res",
    "xlnet_qimai_test_dataset_epoch6_res"
]

qimai_addition_test_res_names = [
    "bert_qimai_addition_test_dataset_epoch5_res",
    "bert_qimai_addition_test_dataset_epoch6_res",
    "xlnet_qimai_addition_test_dataset_epoch5_res",
    "xlnet_qimai_addition_test_dataset_epoch6_res"
]

search_test_res_names = [
    "bert_baidu_test_dataset1_epoch2_res",
    "bert_baidu_test_dataset2_epoch2_res",
    "bert_bing_test_dataset1_epoch2_res",
    "bert_bing_test_dataset2_epoch2_res",
    "xlnet_baidu_test_dataset1_epoch2_res",
    "xlnet_baidu_test_dataset2_epoch2_res",
    "xlnet_bing_test_dataset1_epoch2_res",
    "xlnet_bing_test_dataset2_epoch2_res",
]


def get_pred_prob(name_list):
    res = []
    for name in name_list:
        model_res = pickle_load(path_model_output / f"{name}.pkl")
        res.append(torch.softmax(model_res, 1))
    return torch.mean(torch.stack(res), dim=0)


def get_sorted_index(id_list):
    return sorted(range(len(id_list)), key=lambda k: id_list[k])


def get_submission_id():
    all_submission = os.listdir(path_submission)
    all_id = re.findall("final_test_(\\d+)\\.csv", "|".join(all_submission))
    if all_id:
        return max([int(x) for x in all_id]) + 1
    else:
        return 1


def main(submission_id=None):
    le = pickle_load(path_cache / "apptype_le.pkl")
    test_df = pickle_load(path_cache / "test_df.pkl")

    search_test_pred_prob = get_pred_prob(search_test_res_names)
    qimai_test_pred_prob = get_pred_prob(qimai_test_res_names)
    qimai_addition_test_pred_prob = get_pred_prob(qimai_addition_test_res_names)
    exact_pred_prob = pickle_load(path_cache / "exact_pred_prob.pkl")

    qimai_test_id = pickle_load(path_cache / "bert_qimai_test_id.pkl")
    qimai_addition_test_id = pickle_load(path_cache / "qimai_addition_test_id.pkl")
    exact_pred_id = pickle_load(path_cache / "exact_pred_id.pkl")

    assert len(test_df) == len(search_test_pred_prob)
    assert len(qimai_test_id) == len(qimai_test_pred_prob)
    assert len(qimai_addition_test_id) == len(qimai_addition_test_pred_prob)
    assert len(exact_pred_id) == len(exact_pred_prob)

    new_qimai_test_id = pd.DataFrame(pd.Series(qimai_test_id), columns=["id"])
    new_qimai_test_id["needed"] = True
    qimai_test_id_index1 = test_df.merge(new_qimai_test_id, how="left", on="id")
    qimai_row_mask = qimai_test_id_index1["needed"].fillna(False)
    qimai_test_id_index1 = qimai_test_id_index1.loc[qimai_row_mask]
    qimai_test_id_index1 = qimai_test_id_index1.sort_values("id").index.tolist()
    qimai_test_id_index2 = get_sorted_index(qimai_test_id)

    new_qimai_addition_test_id = pd.DataFrame(pd.Series(qimai_addition_test_id), columns=["id"])
    new_qimai_addition_test_id["needed"] = True
    qimai_addition_test_id_index1 = test_df.merge(new_qimai_addition_test_id, how="left", on="id")
    qimai_addition_row_mask = qimai_addition_test_id_index1["needed"].fillna(False)
    qimai_addition_test_id_index1 = qimai_addition_test_id_index1.loc[qimai_addition_row_mask]
    qimai_addition_test_id_index1 = qimai_addition_test_id_index1.sort_values("id").index.tolist()
    qimai_addition_test_id_index2 = get_sorted_index(qimai_addition_test_id)

    new_exact_pred_id = pd.DataFrame(pd.Series(exact_pred_id), columns=["id"])
    new_exact_pred_id["needed"] = True
    exact_pred_id_index1 = test_df.merge(new_exact_pred_id, how="left", on="id")
    exact_row_mask = exact_pred_id_index1["needed"].fillna(False)
    exact_pred_id_index1 = exact_pred_id_index1.loc[exact_row_mask]
    exact_pred_id_index1 = exact_pred_id_index1.sort_values("id").index.tolist()
    exact_pred_id_index2 = get_sorted_index(exact_pred_id)

    final_test_pred_prob = search_test_pred_prob.clone().detach()
    final_test_pred_prob[qimai_test_id_index1] += qimai_test_pred_prob[qimai_test_id_index2] * 1.2
    final_test_pred_prob[qimai_test_id_index1] /= 2.2
    final_test_pred_prob[qimai_addition_test_id_index1] += \
        qimai_addition_test_pred_prob[qimai_addition_test_id_index2]
    final_test_pred_prob[qimai_addition_test_id_index1] /= 2
    final_test_pred_prob[exact_pred_id_index1] += exact_pred_prob[exact_pred_id_index2]
    final_test_pred_prob[exact_pred_id_index1] /= 2

    final_res = le.inverse_transform((final_test_pred_prob).topk(2, 1)[1].reshape(-1)).reshape(-1, 2)
    final_res = pd.DataFrame(final_res, columns=["label1", "label2"])
    final_res["id"] = test_df["id"]
    submission_id = submission_id if submission_id is not None else get_submission_id()
    filename = path_submission / f"final_test_{submission_id}.csv"
    final_res[["id", "label1", "label2"]].to_csv(filename, index=False)


if __name__ == "__main__":
    main()
