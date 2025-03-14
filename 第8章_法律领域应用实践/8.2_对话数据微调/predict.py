from glm3.modeling_chatglm import ChatGLMForConditionalGeneration
from glm3.tokenization_chatglm import ChatGLMTokenizer
from peft import PeftModel
import torch

# 模型生成方法
def diy_generate(model,tokenizer,text):
    with torch.no_grad():
        ids = tokenizer.encode(text)
        input_ids = torch.LongTensor([ids]).cuda()
        output = model.generate(
            input_ids=input_ids,
            min_length=20,
            max_length=512,
            do_sample=False,
            num_return_sequences=1
        )[0]
        output = tokenizer.decode(output)
        # 美化输出
        if '<|assistant|>' in output:
            output=output.split('<|assistant|>')[-1]
        else:
            output=output.split('\n',1)[-1]
    return output.strip()

# 加载基座模型
model_path='/data/external/资源/预训练模型/chatglm3-6b'
base_model=ChatGLMForConditionalGeneration.from_pretrained(model_path).cuda()
tokenizer=ChatGLMTokenizer.from_pretrained(model_path)

# golden answer
'''根据《公安部-公安机关办理刑事案件程序规定》第一百零八条规定，需经县级以上公安机关负责人批准才能解除取保候审，
并及时通知被取保候审人、保证人和有关单位。如果犯罪嫌疑人正在接受医院治疗且生活不能自理，公安机关可以考虑监视居住。
根据该规定第一百零九条中的规定，患有严重疾病、生活不能自理的犯罪嫌疑人可以被监视居住。
因此，如果一名犯罪嫌疑人正在接受医院治疗且生活不能自理，其可能被监视居住，而无法被解除取保候审。'''

# 基座模型的回答
query='如果一名犯罪嫌疑人正在接受医院治疗且生活不能自理，其是否还能被解除取保候审？'
print(diy_generate(base_model,tokenizer,query))

# 加载微调模型
peft_model=PeftModel.from_pretrained(base_model,'output-glm3/epoch-2-step-11546')
print(diy_generate(peft_model,tokenizer,query))