import argparse
from transformers import AutoConfig, AutoModel, AutoTokenizer
import torch
import os

parser = argparse.ArgumentParser()
parser.add_argument("--pt-checkpoint", type=str, default=None, help="The checkpoint path")
parser.add_argument("--model", type=str, default=None, help="main model weights")
parser.add_argument("--tokenizer", type=str, default=None, help="main model weights")
parser.add_argument("--pt-pre-seq-len", type=int, default=128, help="The pre-seq-len used in p-tuning")
parser.add_argument("--device", type=str, default="cuda")
parser.add_argument("--max-new-tokens", type=int, default=128)
# 增加参数测试集路径
parser.add_argument("--test_path",type=str,default=None,help='test dataset path')
parser.add_argument("--output",type=str,default=None,help="output path")

args = parser.parse_args()

if args.tokenizer is None:
    args.tokenizer = args.model

# 加载模型
if args.pt_checkpoint:
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=True)
    config = AutoConfig.from_pretrained(args.model, trust_remote_code=True, pre_seq_len=128)
    model = AutoModel.from_pretrained(args.model, config=config, trust_remote_code=True)
    prefix_state_dict = torch.load(os.path.join(args.pt_checkpoint, "pytorch_model.bin"))
    new_prefix_state_dict = {}
    for k, v in prefix_state_dict.items():
        if k.startswith("transformer.prefix_encoder."):
            new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
    model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
else:
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=True)
    model = AutoModel.from_pretrained(args.model, trust_remote_code=True)

model = model.to(args.device)

import json
# 读取测试集
with open(args.test_path,'r',encoding='utf-8') as f:
    test_data=json.load(f)
f.close()

query=[]
truth_result=[]

# 预测测试集的内容
for data in test_data:
    query.append(data["prompt"])
    truth_result.append(data["response"])
inputs = tokenizer(query,return_tensors="pt",max_length=512,padding=True,truncation=True)
inputs = inputs.to(args.device)
response = model.generate(input_ids=inputs["input_ids"], max_length=inputs["input_ids"].shape[-1] + args.max_new_tokens)
response = response[:, inputs["input_ids"].shape[-1]:]
pred_result=[tokenizer.decode(rsp, skip_special_tokens=True) for rsp in response]

result=[{'truth_label':truth_result[i],
         'pred_label':pred_result[i]} for i in range(len(pred_result))]

# 将预测结果写入文件
with open(args.output+"/result.json",'w',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
f.close()

# 计算Rouge
import jieba
from rouge_chinese import Rouge
import numpy as np
rouge=Rouge()
scores=[]
for i in range(len(pred_result)):
    pred=list(jieba.cut(pred_result[i]))
    truth=list(jieba.cut(truth_result[i]))
    try:
        scores.append(rouge.get_scores(' '.join(pred),' '.join(truth))[0])
    except:
        None

rouge_1=[]
rouge_2=[]
rouge_l=[]
for sc in scores:
    rouge_1.append(sc['rouge-1']['f'])
    rouge_2.append(sc['rouge-2']['f'])
    rouge_l.append(sc['rouge-l']['f'])
print('Rouge-1:',sum(rouge_1)/len(rouge_1))
print('Rouge-2:',sum(rouge_2)/len(rouge_2))
print('Rouge-l:',sum(rouge_l)/len(rouge_l))