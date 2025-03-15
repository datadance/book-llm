from mmengine.config import read_base

# with read_base():
#     from .datasets.demo.demo_gsm8k_chat_gen import gsm8k_datasets
#     from .datasets.demo.demo_math_chat_gen import math_datasets
#     from .models.qwen.hf_qwen2_1_5b_instruct import models as hf_qwen2_1_5b_instruct_models
#     from .models.hf_internlm.hf_internlm2_chat_1_8b import models as hf_internlm2_chat_1_8b_models

# datasets = gsm8k_datasets + math_datasets
# models = hf_qwen2_1_5b_instruct_models + hf_internlm2_chat_1_8b_models



with read_base():
    from .datasets.cmb.cmb_gen_dfb5c4 import cmb_datasets
    from .models.chatglm.hf_glm4_9b_chat import models as hf_glm4_9b_models

datasets = cmb_datasets
models = hf_glm4_9b_models
