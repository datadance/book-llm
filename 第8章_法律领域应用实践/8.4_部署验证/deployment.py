import gradio as gr
from fastapi import FastAPI
from transformers import AutoTokenizer, AutoModel,AutoConfig
import torch

# model_path:基座模型，chatglm3的存放位置
model_path='/data/external/资源/预训练模型/chatglm3-6b'
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
config = AutoConfig.from_pretrained(model_path, trust_remote_code=True, pre_seq_len=128)
model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True)
model.eval()
model.cuda()

# 将ptuning微调得到的参数拼接到chatglm3中,torch.load中填入指令微调后adapter存放的位置
# 在实验路径下已有微调好的adapter，如果要换成自己的请自行更换
prefix_state_dict = torch.load('../8.3_指令微调/output/instruction_finetune-20250312-215505-128-2e-2/pytorch_model.bin')
new_prefix_state_dict = {}
for k, v in prefix_state_dict.items():
    if k.startswith("transformer.prefix_encoder."):
        new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)

def llm_generate(model,tokenizer,query):
    inputs=tokenizer(query,return_tensors='pt')
    inputs=inputs.to("cuda")
    response = model.generate(input_ids=inputs["input_ids"], max_length=128)
    response = response[0, inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(response, skip_special_tokens=True)

def get_response(function,query):
    if function=='':
        raise gr.Error('未选择正确的功能')
    elif query=='':
        raise gr.Error('未输入查询的罪名')
    else:
        query_dict={
            '查询概念':'查询以下罪名的概念：',
            '查询特征':'查询以下罪名的特征：',
            '查询司法解释':'查询以下罪名的司法解释：'
        }
        ins_query=query_dict[function]+query
        return llm_generate(model,tokenizer,ins_query)

with gr.Blocks(title='法律罪名查询功能') as demo:
    drop_down=gr.Dropdown(choices=['查询概念','查询特征','查询司法解释'],label='请选择具体的功能')
    query=gr.Textbox(label='请输入查询的罪名:')
    btn=gr.Button(value='查询')
    btn.click(get_response,inputs=[drop_down,query],outputs=gr.Markdown())

app=FastAPI()
@app.get('/')
def read_main():
    return {'message':'欢迎使用法律大模型问答系统'}
app=gr.mount_gradio_app(app,demo,path='/lawchat')


import uvicorn
# host请填写服务器id，如果代码部署在本地可删除host参数
# port根据实际情况设置
uvicorn.run(app,host='127.0.0.1',port=8009)