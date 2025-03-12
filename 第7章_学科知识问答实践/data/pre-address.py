import os
# 获取当前路径
current_path = os.getcwd()
# 拼接processed文件夹路径
processed_folder_path = os.path.join(current_path, "processed")
# 判断processed文件夹是否存在
if not os.path.exists(processed_folder_path):
    # 如果不存在则创建processed文件夹
    os.mkdir(processed_folder_path)

# 处理knowledge_url.txt
with open("knowledge_url.txt", 'r', encoding='utf-8') as f:
    ku_data=f.readlines()
f.close()
ku_data=[data.rstrip().split(' ') for data in ku_data]

fwrite=open('./processed/knowledge_url.txt','w',encoding='utf-8')
for i in ku_data:
    fwrite.write(i[0]+' 参考网页：'+i[1]+'\n\n')
fwrite.close()

# 处理knowledge_ppt.txt
with open("knowledge_ppt.txt", 'r', encoding='utf-8') as f:
    kp_data=f.readlines()
f.close()
kp_data=[data.rstrip().split(' ',1) for data in kp_data]

fwrite=open('./processed/knowledge_ppt.txt','w',encoding='utf-8')
for i in kp_data:
    if len(i) == 1:
        fwrite.write(i[0]+' 本知识点暂无本地资源可参考。\n\n')
    else:
        fwrite.write(i[0]+' 可参考本地资源：'+i[1]+'\n\n')
fwrite.close()

# 处理nlp_triple.txt
with open("nlp_triple.txt", 'r', encoding='utf-8') as f:
    nt_data=f.readlines()
f.close()
nt_data=[data.rstrip().split(' ') for data in nt_data]
knowledge_dict={}
for i in nt_data:
    try:
        key=(i[0],i[1])
        if key in knowledge_dict:
            knowledge_dict[key].append(i[2])
        else:
            knowledge_dict[key]=[i[2]]
    except:
        None

fwrite=open('./processed/nlp_triple.txt','w',encoding='utf-8')
for k in knowledge_dict:
    value=knowledge_dict[k]
    head,rel=k
    if rel == '包含':
        fwrite.write(head+' 推荐继续学习以下知识点：'+' '.join(value)+'\n\n')
    else:
        fwrite.write(head+' 学习该知识点前需要具备以下知识：'+' '.join(value)+'\n\n')
fwrite.close()