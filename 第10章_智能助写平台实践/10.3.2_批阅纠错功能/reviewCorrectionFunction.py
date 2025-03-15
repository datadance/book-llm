#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   reviewCorrectionFunction.py
@Time    :   2025/03/15 15:08:09
@Author  :   iflytek
@Version :   1.0
@Desc    :   批阅纠错功能核心代码
'''


from fastapi import APIRouter, Depends,HTTPException
from deps.depends import get_db,get_redis_client
from dao import crud
from bo import schemas
from log.log import logger
from sqlalchemy.orm import Session
from utils.count_word import count_word,count_word_intercept
import uuid
import json
from dao import models

router = APIRouter()
# 使用router获取post请求的数据
@router.post("/single_paragraph")
async def single_paragraph(input_text: schemas.InputText, db:Session = Depends(get_db), redis_client=Depends(get_redis_client)):
  # 验证Token
  token_str = input_text.access_token
  user = crud.get_current_user(token_str,db)
  if not count_word_intercept(input_text.text, input_text.input_language):
    return {
      "status": "error",
      "message": "输入文本字数过长"
    }
  content = input_text.text
  prompt_index = input_text.prompt_index
  prompt_intensity_index = input_text.prompt_intensity_index
  input_language = input_text.input_language

  prompt_hash_redis_field = 'prompt'
  if not redis_client.hexists(prompt_hash_redis_field, prompt_index) == None:
    prompt = crud.get_prompt_content(db, input_language, prompt_index)
  
  prompt_intensity_hash_redis_field = 'prompt_intensity'
  if not redis_client.hexists(prompt_intensity_hash_redis_field, prompt_intensity_index) == None:
    prompt_intensity = crud.get_prompt_intensity_content(db, input_language, prompt_intensity_index)
    
  if input_language == 0:
    prompt_template = "and provide only a corrected version of the text."
  elif input_language == 1:
    prompt_template = "请只提供更正后的文本。"

  word_num = count_word(content)
  #print('hahha',db.query(models.User).filter(models.User.id == user.id).first().initial_token,crud.get_user_all_token_num(db,user.id),word_num)
  if(db.query(models.User).filter(models.User.id == user.id).first().initial_token - crud.get_user_all_token_num(db,user.id) - word_num< 0):
    return {
      "status":"error",
      "message":"您的剩余Token已不够，请增加您的token上限"
    }
  crud.update_user_token_num(db, user.id, prompt_index, word_num)
  instruction = prompt + prompt_intensity + prompt_template
  generated_uuid = str(uuid.uuid4()) # 32
  sent_uuid = generated_uuid + str(user.id)
  llm_params = {"instruction": instruction, "input": content, 
        "payload":{"prompt_index":prompt_index,"prompt_intensity_index":prompt_intensity_index}}
  llm_params = json.dumps(llm_params)
  if redis_client.set(sent_uuid, llm_params) and redis_client.expire(sent_uuid, 60 * 10):
    return {"uuid":sent_uuid,"status":"success","message":"消息发送成功"}
  else:
    raise HTTPException(status_code=404, detail="Something Wrong in redis")

@router.post("/single_paragraph_other")
async def single_paragraph_other(input_text: schemas.InputNewText, db:Session = Depends(get_db), redis_client=Depends(get_redis_client)):
  # 验证Token
  token_str = input_text.access_token
  user = crud.get_current_user(token_str,db)
  if not count_word_intercept(input_text.text, 1):
    return {
      "status": "error",
      "message": "输入文本字数过长"
    }
  content = input_text.text
  prompt_index = input_text.prompt_index
  prompt_intensity_index = input_text.prompt_intensity_index

  prompt_hash_redis_field = 'prompt'
  if not redis_client.hexists(prompt_hash_redis_field, prompt_index) == None:
    if input_text.input_language == 1:
      prompt = crud.get_prompt_content(db, 0, prompt_index)
    else:
      if prompt_index % 3 == 0:
        prompt = crud.get_prompt_content(db, 0, 3)
      else:
        prompt = crud.get_prompt_content(db, 0, prompt_index % 3)
  
  prompt_intensity_hash_redis_field = 'prompt_intensity'
  if not redis_client.hexists(prompt_intensity_hash_redis_field, prompt_intensity_index) == None:
    if input_text.input_language == 1:
      prompt_intensity = crud.get_prompt_intensity_content(db, 1, prompt_intensity_index)
    else:
      prompt_intensity = crud.get_prompt_intensity_content(db, 0, prompt_intensity_index)
  if input_text.input_language == 1:
    prompt_template = "请只提供更正后的文本。"
  else:
    prompt_template = "and provide only a corrected version of the text."

  word_num = count_word(content)
  #print('hahha',db.query(models.User).filter(models.User.id == user.id).first().initial_token,crud.get_user_all_token_num(db,user.id),word_num)
  if(db.query(models.User).filter(models.User.id == user.id).first().initial_token - crud.get_user_all_token_num(db,user.id) - word_num< 0):
    return {
      "status":"error",
      "message":"您的token余额已不够，请邀请其他人增加您的token上限"
    }
  crud.update_user_token_num(db, user.id, prompt_index, word_num)
  instruction = prompt + prompt_intensity + prompt_template
  generated_uuid = str(uuid.uuid4()) # 32
  sent_uuid = generated_uuid + str(user.id)
  llm_params = {"instruction": instruction, "input": content, 
        "payload":{"prompt_index":prompt_index,"prompt_intensity_index":prompt_intensity_index}}
  llm_params = json.dumps(llm_params)
  if redis_client.set(sent_uuid, llm_params):
    return {"uuid":sent_uuid,"status":"success","message":"消息发送成功"}
  else:
    raise HTTPException(status_code=404, detail="Something Wrong in redis")
  
@router.get('/prompts')
def getPrompts(db: Session = Depends(get_db)):
  # 临时处理，删除最后一个Prompt，可以考虑加一个字段
  prompt_list = crud.get_prompts_title(db)
  list_size = len(prompt_list) - 1

  result_list = {}
  for i in range(1,list_size - 1):
    result_list[i] = prompt_list[i]
  list_size = list_size - 1
  return {"size": list_size, "list": prompt_list}