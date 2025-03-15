#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   personalCenterFunction.py
@Time    :   2025/03/15 15:13:27
@Author  :   whwang22
@Version :   1.0
@Desc    :   个人中心功能核心代码
'''


@router.post("/token_num_specify_day")
# 使用router获取post请求的数据
def get_token_num(user_token: schemas.SpecifyTokenNum, db: Session = Depends(get_db)):
  token_str = user_token.access_token
  user = crud.get_current_user(token_str, db)
  user_id = user.id
  # utc_tz = pytz.timezone('Asia/Shanghai')
  # time = datetime.now(utc_tz)
  time = {
    "year": user_token.year,
    "month": user_token.month
  }
  # res_token = {}
  res_token = []
  _, last_day = calendar.monthrange(time["year"], time["month"])
  prompt_array = []
  if user_token.prompt_index == 2:
    prompt_array.append(4)
  elif user_token.prompt_index == 3:
    prompt_array.append(5)
  elif user_token.prompt_index == 1:
    prompt_array.extend([1, 2, 3])
  elif user_token.prompt_index == 0:
    prompt_array.extend([1, 2, 3, 4, 5])
  for i in range(1, last_day + 1):
    cur_day = date(time["year"], time["month"], i)
    temp_num = db.query(func.sum(models.Count.token_num).label('count')).filter(user_id == models.Count.UID,models.Count.date == cur_day,models.Count.cate.in_(prompt_array)).first()
    # res_token[i] = temp_num.count if temp_num.count is not None else 0
    num = temp_num.count if temp_num.count is not None else 0
    res_token.append(num)
  if user:
    logger.info('get_user_token_num: ' + user.user_name + ' get_user_token_num success')
    return {"status": "success", "message": "查询成功", 'month_token': res_token}
  else:
    logger.error('get_user_token_num: ' + user.user_name + ' get_user_token_num error')
    return {"status": "error", "message": "查询失败"}

# 获取每个用户的剩余Token数，总共token = 1e6
@router.post("/cur_token")
def get_cur_token(user_token: schemas.UserToken, db: Session = Depends(get_db)):
  token_str = user_token.access_token
  user = crud.get_current_user(token_str, db)
  if user:
    logger.info('查询用户成功' + user.user_name)
  else:
    logger.error('查询用户失败')
  user_id = user.id
  all_token = crud.get_user_all_token_num(db, user_id)
  initial_token = db.query(models.User).filter(models.User.id == user_id).first().initial_token
  # print(type(all_token),type(1e6))
  if all_token >= 0:
    logger.info('查询总token成功')
    return {
      "status": "success",
      "message": "查询成功",
      "all_token_num": initial_token - all_token,
      "total_token_num": initial_token
    }
  else:
    logger.error("查询总token失败")
    return {
      "status": "error",
      "message": "查询失败"
    }