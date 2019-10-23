python modeling.py train \
    --model_type bert \
    --model_name qimai \
    --dataset_name chusai_dataset \
    --epoch_num 6 \
    --batch_size_per_gpu 7 \
    --gpu_device_ids 0 \
    --gradient_accumulation_steps 16 \
    --warmup_proportion 0.1 \
    --learning_rate 5e-5 \
    --seed 1

python modeling.py train \
    --model_type xlnet \
    --model_name qimai \
    --dataset_name chusai_dataset \
    --epoch_num 6 \
    --batch_size_per_gpu 2 \
    --gpu_device_ids 0 \
    --gradient_accumulation_steps 64 \
    --warmup_proportion 0.1 \
    --learning_rate 5e-5 \
    --seed 2

python modeling.py train \
    --model_type bert \
    --model_name baidu \
    --dataset_name baidu_dataset1 baidu_dataset2 \
    --epoch_num 3 \
    --batch_size_per_gpu 7 \
    --gpu_device_ids 0  \
    --gradient_accumulation_steps 16 \
    --warmup_proportion 0.1 \
    --learning_rate 5e-5 \
    --seed 11

python modeling.py train \
    --model_type xlnet \
    --model_name baidu \
    --dataset_name baidu_dataset1 baidu_dataset2 \
    --epoch_num 3 \
    --batch_size_per_gpu 2 \
    --gpu_device_ids 0 \
    --gradient_accumulation_steps 64 \
    --warmup_proportion 0.1 \
    --learning_rate 5e-5 \
    --seed 12

python modeling.py train \
    --model_type bert \
    --model_name bing \
    --dataset_name bing_dataset1 bing_dataset2 \
    --epoch_num 3 \
    --batch_size_per_gpu 7 \
    --gpu_device_ids 0 \
    --gradient_accumulation_steps 16 \
    --warmup_proportion 0.1 \
    --learning_rate 5e-5 \
    --seed 21

python modeling.py train \
    --model_type xlnet \
    --model_name bing \
    --dataset_name bing_dataset1 bing_dataset2 \
    --epoch_num 3 \
    --batch_size_per_gpu 2 \
    --gpu_device_ids 0 \
    --gradient_accumulation_steps 64 \
    --warmup_proportion 0.1 \
    --learning_rate 5e-5 \
    --seed 22
