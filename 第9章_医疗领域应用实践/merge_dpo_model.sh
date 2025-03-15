cd ./MedicalGPT/
python merge_peft_adapter.py \
--model_type chatglm \
--base_model glm4-sft-merged \
--lora_model glm4-dpo-v1 \
--output_dir ./glm4-dpo-merged