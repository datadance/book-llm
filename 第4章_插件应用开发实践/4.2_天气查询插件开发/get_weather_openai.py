# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : get_weather_openai.py
# @Author: iflytek
# @Desc  : 天气查询插件开发

import os
import pprint
import json
import openai
import requests
from area import CITIES


from openai import OpenAI


client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="******",
    base_url="https://api.chatanywhere.tech/v1"
)



def get_weather(city_name: str):
    url = "https://restapi.amap.com/v3/weather/weatherInfo?"

    params = {"key": "******",
              "city": "110000",
              "extensions": "all"}
    city_code = "110000"

    for city in CITIES:
        if city_name in city.get("city"):
            city_code = city.get("adcode")
            break
    params['city'] = city_code

    response = requests.get(url=url, params=params)
    pprint.pprint(response.json())
    return response.json().get("forecasts")[0].get("casts")



def run_conversation(question):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question}],
        functions=[
            {
                "name": "get_weather",
                "description": "获取指定地区的当前天气情况",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city_name": {
                            "type": "string",
                            "description": "城市，例如：深圳",
                        },
                    },
                    "required": ["city_name"],
                },
            }
        ],
        function_call="auto",
    )
    print(response.to_json())
    message = response.choices[0].message
    function_call = message.function_call
    if function_call:
        arguments = function_call.arguments
        print("arguments",arguments)
        arguments = json.loads(arguments)
        function_response = get_weather(city_name=arguments.get("city_name"),)
        function_response = json.dumps(function_response)
        return function_response
    else:
        return response
    

def gpt_summary(function_response,question):
    """
    TODO: GPT总结处理
    """
    
    second_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": question},

            {
                "role": "function",
                "name": "get_weather",
                "content": function_response,
            },
        ],
    )
    print(second_response)
    return second_response


if __name__ == '__main__':
    question = "合肥市天气如何？"
    function_response = run_conversation(question)
    gpt_response=gpt_summary(function_response,question)
    content = gpt_response.choices[0].message.content
    print("content:", content)