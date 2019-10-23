python modeling.py predict \
    --model_type bert \
    --model_name qimai \
    --dataset_name qimai_addition_test_dataset \
    --epoch_num 5 \
    --batch_size_per_gpu 64 \
    --gpu_device_ids 0
python modeling.py predict \
    --model_type bert \
    --model_name qimai \
    --dataset_name qimai_addition_test_dataset \
    --epoch_num 6 \
    --batch_size_per_gpu 64 \
    --gpu_device_ids 0
python modeling.py predict \
    --model_type xlnet \
    --model_name qimai \
    --dataset_name qimai_addition_test_dataset \
    --epoch_num 5 \
    --batch_size_per_gpu 64 \
    --gpu_device_ids 0
python modeling.py predict \
    --model_type xlnet \
    --model_name qimai \
    --dataset_name qimai_addition_test_dataset \
    --epoch_num 6 \
    --batch_size_per_gpu 64 \
    --gpu_device_ids 0

python modeling.py predict \
    --model_type bert \
    --model_name baidu \
    --dataset_name baidu_test_dataset1 baidu_test_dataset2 \
    --epoch_num 2 \
    --batch_size_per_gpu 64 \
    --gpu_device_ids 0
python modeling.py predict \
    --model_type bert \
    --model_name bing \
    --dataset_name bing_test_dataset1 bing_test_dataset2 \
    --epoch_num 2 \
    --batch_size_per_gpu 64 \
    --gpu_device_ids 0
python modeling.py predict \
    --model_type xlnet \
    --model_name baidu \
    --dataset_name baidu_test_dataset1 baidu_test_dataset2 \
    --epoch_num 2 \
    --batch_size_per_gpu 64 \
    --gpu_device_ids 0
python modeling.py predict \
    --model_type xlnet \
    --model_name bing \
    --dataset_name bing_test_dataset1 bing_test_dataset2 \
    --epoch_num 2 \
    --batch_size_per_gpu 64 \
    --gpu_device_ids 0
