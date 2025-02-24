# Huggingface SDK下载方法
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)
model = AutoModel.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)

# Modelscope SDK下载方法
from modelscope import snapshot_download
model_dir = snapshot_download('ZhipuAI/chatglm3-6b')