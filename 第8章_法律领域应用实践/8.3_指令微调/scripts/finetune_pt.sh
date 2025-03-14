#! /usr/bin/env bash

set -ex

# ptuning时soft prompt的长度
PRE_SEQ_LEN=128
# 学习率
LR=2e-2
# 使用的GPU数量
NUM_GPUS=1
# 输入文本最大的长度
MAX_SOURCE_LEN=64
# 输出文本的最大长度
MAX_TARGET_LEN=256
# batch size
DEV_BATCH_SIZE=1
# 梯度累计
GRAD_ACCUMULARION_STEPS=16
# 训练步数
MAX_STEP=1000
# 每500步保存一个模型
SAVE_INTERVAL=500

# 时间戳
DATESTR=`date +%Y%m%d-%H%M%S`
# 任务名称(可自定义)
RUN_NAME=instruction_finetune

# ChatGLM3的模型路径
BASE_MODEL_PATH=/data/external/资源/预训练模型/chatglm3-6b
# 数据集的路径
DATASET_PATH=../data/processed/instruction_data_train.json
# 模型输出路径
OUTPUT_DIR=../output/${RUN_NAME}-${DATESTR}-${PRE_SEQ_LEN}-${LR}

mkdir -p $OUTPUT_DIR

torchrun --standalone --nnodes=1 --nproc_per_node=$NUM_GPUS ../finetune.py \
    --train_format input-output \
    --train_file $DATASET_PATH \
    --preprocessing_num_workers 1 \
    --model_name_or_path $BASE_MODEL_PATH \
    --output_dir $OUTPUT_DIR \
    --max_source_length $MAX_SOURCE_LEN \
    --max_target_length $MAX_TARGET_LEN \
    --per_device_train_batch_size $DEV_BATCH_SIZE \
    --gradient_accumulation_steps $GRAD_ACCUMULARION_STEPS \
    --max_steps $MAX_STEP \
    --logging_steps 1 \
    --save_steps $SAVE_INTERVAL \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN 2>&1 | tee ${OUTPUT_DIR}/train.log
