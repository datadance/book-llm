# 读取未处理的数据
with open('./data/raw/kg_crime.json','r',encoding='utf-8') as f:
    kg_data=f.readlines()
f.close()
kg_data=[eval(i.rstrip()) for i in kg_data]

# 概念、特征和解释
gainian_instruction="查询以下罪名的概念："
tezheng_instruction="查询以下罪名的特征："
jieshi_instruction="查询以下罪名的司法解释："

# 构建指令数据
instruction_data=[]
for data in kg_data:
    crime_name=data['crime_small']
    instruction_data.append({
        "prompt":gainian_instruction+crime_name,
        "response":data['gainian'][0]
    })
    instruction_data.append({
        "prompt":tezheng_instruction+crime_name,
        "response":''.join(data['tezheng'])
    })
    invalid_jieshi="本罪名没有司法解释。"
    if len(data['jieshi']) != 0:
        instruction_data.append({
            "prompt":jieshi_instruction+crime_name,
            "response":''.join(data['jieshi'])
        })
    else:
        instruction_data.append({
            "prompt":jieshi_instruction+crime_name,
            "response":invalid_jieshi
        })

# 将处理的结果写入文件
import json
with open('./data/processed/instruction_data_train.json','w',encoding='utf-8') as f:
    json.dump(instruction_data,f,ensure_ascii=False,indent=2)
f.close()

# 随机选取数据构建测试集
import random
with open('./data/processed/instruction_data_test.json','w',encoding='utf-8') as f:
    json.dump(random.sample(instruction_data,int(len(kg_data)*0.2)),f,ensure_ascii=False,indent=2)
f.close()