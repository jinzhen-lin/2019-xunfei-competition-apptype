# -*- coding: utf-8 -*-
import argparse
import os

import torch
from pytorch_transformers import (
    AdamW, WarmupLinearSchedule,
    BertForSequenceClassification, 
    XLNetForSequenceClassification
)
from torch import nn
from torch.utils.data import ConcatDataset, DataLoader
from tqdm.auto import tqdm, trange

from apptype_utils import *


def train_model(args):
    set_seed(args.seed)

    train_dataset = [
        path_tensor_dataset / f"{args.model_type}_{x}.pkl" for x in args.dataset_name
    ]
    train_dataset = [pickle_load(x) for x in train_dataset]
    train_dataset = ConcatDataset(train_dataset)
    train_dataloader = DataLoader(
        train_dataset, batch_size=args.batch_size, 
        pin_memory=True, num_workers=4, shuffle=True
    )

    if args.model_type == "bert":
        model = BertForSequenceClassification.from_pretrained(path_bert_model, num_labels=126)
    elif args.model_type == "xlnet":
        model = XLNetForSequenceClassification.from_pretrained(path_xlnet_model, num_labels=126)
    else:
        raise ValueError("")
    model.zero_grad()
    model = model.cuda(args.gpu_device_ids[0])
    if args.n_gpu > 1:
        model = torch.nn.DataParallel(model, device_ids=args.gpu_device_ids)

    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {"params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)], "weight_decay": 0.01},
        {"params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)], "weight_decay": 0.0}
    ]
    optimizer = AdamW(optimizer_grouped_parameters, lr=args.learning_rate)

    total_steps = len(train_dataloader) * args.epoch_num // args.gradient_accumulation_steps
    warmup_steps = int(total_steps * args.warmup_proportion)
    scheduler = WarmupLinearSchedule(optimizer, warmup_steps=warmup_steps, t_total=total_steps)

    global_step = 0
    train_iterator = trange(int(args.epoch_num), desc="Epoch")
    for i in train_iterator:
        epoch = i + 1
        epoch_iterator = tqdm(train_dataloader, desc="Iteration")
        for batch in epoch_iterator:
            model.train()
            batch = tuple(x.cuda(args.gpu_device_ids[0]) for x in batch)
            inputs = {
                "input_ids": batch[0],
                "attention_mask": batch[1],
                "token_type_ids": batch[2],
                "labels":  batch[3]
            }
            outputs = model(**inputs)
            loss = outputs[0]
            if args.n_gpu > 1:
                loss = loss.mean()
            loss.backward()
            if global_step % args.gradient_accumulation_steps == 0:
                optimizer.step()
                scheduler.step()
                model.zero_grad()
            global_step += 1

        output_dir = f"{args.model_type}_{args.model_name}/checkpoint_epoch{epoch}"
        output_dir = path_model / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        model_to_save = model.module if hasattr(model, "module") else model
        model_to_save.save_pretrained(output_dir)
        pickle_save(args, os.path.join(output_dir, "training_args.pkl"))


def predict_model(args, save=True):
    dataset_name = args.dataset_name[0]
    model_type = args.model_type
    test_dataset = path_tensor_dataset / f"{model_type}_{dataset_name}.pkl"
    test_dataset = pickle_load(test_dataset)
    test_dataloader = DataLoader(
        test_dataset, batch_size=args.batch_size,
        pin_memory=True, num_workers=4, shuffle=False
    )

    model_dir = path_model / f"{args.model_type}_{args.model_name}/checkpoint_epoch{args.epoch_num}"
    if model_type == "bert":
        model = BertForSequenceClassification.from_pretrained(model_dir, num_labels=126)
    elif model_type == "xlnet":
        model = XLNetForSequenceClassification.from_pretrained(model_dir, num_labels=126)
    else:
        raise ValueError("")
    model.zero_grad()
    model.eval()
    model = model.cuda(args.gpu_device_ids[0])
    if args.n_gpu > 1:
        model = torch.nn.DataParallel(model, device_ids=args.gpu_device_ids)

    res = []
    for batch in tqdm(test_dataloader, desc="Iteration"):
        batch = tuple(x.cuda(args.gpu_device_ids[0]) for x in batch)
        inputs = {
            "input_ids": batch[0],
            "attention_mask": batch[1],
            "token_type_ids": batch[2]
        }
        with torch.no_grad():
            outputs = model(**inputs)[0]
        res.append(outputs)
    res = torch.cat(res, 0).cpu()
    if save:
        filename = f"{model_type}_{dataset_name}_epoch{args.epoch_num}_res.pkl"
        pickle_save(res, path_model_output / filename)
    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", help="训练train或者预测predict", 
        choices=["train", "predict"]
    )
    parser.add_argument("--model_type", help="模型类型：bert或者xlnet", choices=["bert", "xlnet"])
    parser.add_argument("--model_name", help="模型名称，不用包含模型类型名")
    parser.add_argument("--dataset_name", help="用来训练、评测或者预测的数据集", nargs="+")
    parser.add_argument(
        "--epoch_num", type=int, help="训练时：训练多少个epoch；预测时：使用第几个epoch的结果预测"
    )
    parser.add_argument("--batch_size_per_gpu", help="训练/评测/预测时的单GPU的batch_size", type=int)
    parser.add_argument("--gpu_device_ids", help="GPU设备的ID，可为多个", type=int, nargs="+")
    parser.add_argument("--gradient_accumulation_steps", help="梯度累加的步数", type=int)
    parser.add_argument("--warmup_proportion", help="有多少比例的步数用于warmup", type=float)
    parser.add_argument("--learning_rate", help="学习率", type=float)
    parser.add_argument("--seed", help="随机数种子", type=int)

    args = parser.parse_args()
    args.n_gpu = len(args.gpu_device_ids)
    args.batch_size = args.batch_size_per_gpu * args.n_gpu

    if args.action == "train":
        train_model(args)
    elif args.action == "predict":
        dataset_name = args.dataset_name
        for name in dataset_name:
            args.dataset_name = [name]
            predict_model(args, save=True)

if __name__ == "__main__":
    main()
