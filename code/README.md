## 环境依赖

以下为我的运行环境及包版本：

- 操作系统Windows Server 2019 Datacenter （在Linux应该也能正常运行）
- Python 3.7.4 （用3.6+应该就行）
- Pytorch 1.2.0 （能支撑起pytorch_transformers的版本应该都行）
- pytorch_transformers 1.1.0 （用那个新的transformers包应该也行，但import的代码需要改一下）
- 其他一些应该不会因小版本差异而大幅更改行为的包：numpy、pandas、scrapy、tqdm、scikit-learn、requests、lxml、pytorch_transformers、hanziconv、redis、brotl

大部分包使用的是来自conda的版本，当conda没有对应的包时再使用pip安装。所以需要安装一个最新版的miniconda3或者anaconda3

```
conda install pytorch torchvision cudatoolkit=10.0 -c pytorch
conda install numpy pandas scrapy tqdm scikit-learn requests lxml
pip install pytorch_transformers hanziconv redis brotl
```

同时，还需要下载预训练模型。需要从[这里](https://github.com/ymcui/Chinese-BERT-wwm)和[这里](https://github.com/ymcui/Chinese-PreTrained-XLNet)下载Pytorch版本的**BERT-wwm-ext**和**XLNet-mid**模型，分别解压之后**将bert_config.json文件重命名为config.json**。

## 代码说明

- apptype_utils.py ： 这个文件不直接用于运行，而是包含了项目的一些设置文件（主要是各种路径）与有用的函数，用于被其他文件import
- process_rawdata.py ：对原始数据进行简单的预处理，并保存在cache目录下
- process_redisdata.py ：从redis数据库中提取爬取的数据，并进行整合处理，将结果保存在cache目录下。这个文件需要在数据爬取之后再运行。
- generate_dataset.py ：用来根据原始数据与外部数据文件，并输出可以直接作为BERT或XLNet模型输入的数据集。
  - generate_dataset.bat ：里面包含的是用来调用generate_dataset.py来生成全部所需数据集的命令
  - generate_dataset.sh ： 与generate_dataset.bat功能一致，方便在linux下运行
- modeling.py ：包含了用于训练和预测模型的代码
  - train_model.bat ：包含了调用modeling.py来训练全部所需模型的命令，命令里的参数就是我实际使用的模型参数
  - predict_model.bat ：包含了调用modeling.py来预测全部所需模型的命令
  - train_model.sh与predict_model.sh：与相应的bat文件功能一直，方便在linux下运行
- get_exact_pred.py ：对应的就是方法说明中的借助规则匹配来获取对应应用类别
- output_submission.py ：输出提交文件

为了复现只需要将复赛和初赛数据的所有文件（共5个）放在rawdata目录下，**修改code/apptype_utils.py中的各种路径**，之后运行run.bat（或run.sh）即可。但直接这样运行的话多个模型是串行训练的，如果有足够的GPU资源可以拆开来并行训练多个模型，但参数需要进行对应调整。

