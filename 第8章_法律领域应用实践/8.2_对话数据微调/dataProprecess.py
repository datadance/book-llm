import json
# 打开原文件
with open("data/raw/qa_data_train.json","r",encoding="utf-8") as f:
    data=json.load(f)
f.close()

# 将数据集转换成正确的格式
for d in data:
    d["instruction"] = ""
    d["output"] = d["answer"]
    del d["answer"]

# 将文件写到本地
with open("data/processed/chat_data.json","w",encoding="utf-8") as f:
    for d in data:
        json.dump(d,f,ensure_ascii=False)
        f.write('\n')
f.close()