cd ./MedicalGPT/
python merge_peft_adapter.py \
--model_type chatglm \
--base_model /data/whwang22/pretrained_model/glm-4-9b-chat \
--lora_model glm4-pt-v1 \
--output_dir glm4-pt-merged/