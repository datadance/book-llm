#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   smartTranslationFunction.py
@Time    :   2025/03/15 15:10:59
@Author  :   iflytek
@Version :   1.0
@Desc    :   智能翻译功能核心代码
'''


from fastapi import APIRouter, Depends,HTTPException
from deps.depends import get_db,get_redis_client,get_spark, get_write_gpt
from sqlalchemy.orm import Session
from dao import crud
from bo import schemas
from log.log import logger
from utils.count_word import count_word,count_word_intercept
import uuid
import json
from dao import models

router = APIRouter()
# 使用router获取post请求的数据
@router.post("/single_paragraph")
async def chat(input_text: schemas.InputTranslate, db: Session = Depends(get_db), redis_client = Depends(get_redis_client)):
  # 验证Token
  token_str = input_text.access_token
  user = crud.get_current_user(token_str, db)
  if not count_word_intercept(input_text.text, input_text.source_language):
    return {
      "status": "error",
      "message": "输入文本字数过长"
    }
  content = input_text.text
  prompt_index = 4
  source_language = input_text.source_language
  target_language = 1- source_language # 0/1 TODO:多语言待改
  word_num = count_word(content)
  #print('hahha',db.query(models.User).filter(models.User.id == user.id).first().initial_token,crud.get_user_all_token_num(db,user.id),word_num)
  if(db.query(models.User).filter(models.User.id == user.id).first().initial_token - crud.get_user_all_token_num(db,user.id) - word_num< 0):
    return {
      "status":"error",
      "message":"您的剩余Token已不够，请增加您的Token上限"
    }
  crud.update_user_token_num(db, user.id, 4, word_num)
  
  prompt_hash_redis_field = 'prompt'
  if not redis_client.hexists(prompt_hash_redis_field, prompt_index) == None:
    prompt = crud.get_prompt_content(db, source_language, prompt_index) 

  if source_language == 0:
    prompt_template = "Please provide the translated text only."
  elif source_language == 1:
    prompt_template = "只给出翻译后的文本，不包含其他输出。"
  
  instruction = prompt + prompt_template
  generated_uuid = str(uuid.uuid4()) # 32
  sent_uuid = generated_uuid + str(user.id)
  llm_params = {"instruction":instruction, "input":content,
         "payload":{"prompt_index":prompt_index,"prompt_intensity_index":1}}
  llm_params = json.dumps(llm_params)
  if redis_client.set(sent_uuid, llm_params) and redis_client.expire(sent_uuid, 60 * 10):
    return {"uuid":sent_uuid,"status":"success","message":"消息发送成功"}
  else:
    raise HTTPException(status_code=404, detail="Something Wrong in redis") 