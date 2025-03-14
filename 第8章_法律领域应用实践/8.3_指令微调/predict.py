from transformers import AutoTokenizer, AutoModel,AutoConfig
import torch
model_path='/data/external/资源/预训练模型/chatglm3-6b' # 填写基础模型路径
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
config = AutoConfig.from_pretrained(model_path, trust_remote_code=True, pre_seq_len=128)
model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True)
model.eval()
model.cuda()

gainian_query='查询以下罪名的概念：交通肇事罪'
tezheng_query='查询以下罪名的特征：交通肇事罪'
jieshi_query='查询以下罪名的司法解释：交通肇事罪'
response,history=model.chat(tokenizer,gainian_query,history=[])
print('基座模型:\n'+gainian_query+'\n'+response+'\n')

response,history=model.chat(tokenizer,tezheng_query,history=[])
print('基座模型:\n'+tezheng_query+'\n'+response+'\n')

response,history=model.chat(tokenizer,jieshi_query,history=[])
print('基座模型:\n'+jieshi_query+'\n'+response+'\n')

# 将ptuning微调得到的参数拼接到chatglm3中
prefix_state_dict = torch.load('output/instruction_finetune/pytorch_model.bin')
new_prefix_state_dict = {}
for k, v in prefix_state_dict.items():
    if k.startswith("transformer.prefix_encoder."):
        new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)

def get_response(model,tokenizer,query):
    inputs=tokenizer(query,return_tensors='pt')
    inputs=inputs.to("cuda")
    response = model.generate(input_ids=inputs["input_ids"], max_length=128)
    response = response[0, inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(response, skip_special_tokens=True)

response = get_response(model,tokenizer,gainian_query)
print('微调模型:\n'+gainian_query+'\n'+response+'\n')

response = get_response(model,tokenizer,tezheng_query)
print('微调模型:\n'+tezheng_query+'\n'+response+'\n')

response = get_response(model,tokenizer,jieshi_query)
print('微调模型:\n'+jieshi_query+'\n'+response+'\n')
