cd ./MedicalGPT/
CUDA_VISIBLE_DEVICES=0 python inference.py \
--model_type chatglm \
--base_model glm4-dpo-merged \
--tokenizer_path glm4-dpo-merged \
--interactive