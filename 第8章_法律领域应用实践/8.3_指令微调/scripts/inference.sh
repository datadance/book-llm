python ../inference.py \
    --pt-checkpoint ../output/instruction_finetune-20250312-215505-128-2e-2 \
    --model /data/external/资源/预训练模型/chatglm3-6b \
    --tokenizer /data/external/资源/预训练模型/chatglm3-6b \
    --test_path ../data/processed/instruction_data_test.json \
    --output ../