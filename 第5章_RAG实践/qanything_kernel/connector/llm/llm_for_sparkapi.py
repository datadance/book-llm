# -*- coding: utf-8 -*-
import json
import sys
from abc import ABC
from typing import List

import tiktoken

sys.path.append("../../../")
from qanything_kernel.utils.custom_log import debug_logger
from sparkai.core.messages import ChatMessage
from sparkai.llm.llm import ChatSparkLLM, AsyncChunkPrintHandler
from qanything_kernel.connector.llm.base import (BaseAnswer, AnswerResult)
import config

try:
    from dotenv import load_dotenv
except ImportError:
    raise RuntimeError(
        'Python environment for SPARK AI is not completely set up: required package "python-dotenv" is missing.') from None

load_dotenv()


class SparkApi(BaseAnswer, ABC):
    model: str = "gpt-3.5-turbo"
    token_window: int = None
    max_token: int = config.llm_config['max_token']
    offcut_token: int = 50
    truncate_len: int = 50
    temperature: float = 0
    top_p: float = config.llm_config['top_p']    # top_p must be (0,1]
    stop_words: str = None
    history: List[List[str]] = []
    history_len: int = config.llm_config['history_len']
    def __init__(self, args):
        self.SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.5/chat'
        # 星火认知大模型调用秘钥信息，请前往讯飞开放平台控制台（https://console.xfyun.cn/services/bm35）查看
        self.SPARKAI_APP_ID = '979fa3b4'
        self.SPARKAI_API_SECRET = 'NTkwMGU2NGM0YzNjYTM4OGM3MjIwZDkz'
        self.SPARKAI_API_KEY = '6c6d5491a3612a4a2958c916db7e6d85'
        # 星火认知大模型Spark3.5 Max的domain值，其他版本大模型domain值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
        self.SPARKAI_DOMAIN = 'generalv3.5'
        self.token_window = 4096

        self.client = ChatSparkLLM(
            spark_api_url=self.SPARKAI_URL,
            spark_app_id=self.SPARKAI_APP_ID,
            spark_api_key=self.SPARKAI_API_KEY,
            spark_api_secret=self.SPARKAI_API_SECRET,
            spark_llm_domain=self.SPARKAI_DOMAIN,
            streaming=False,
            model_kwargs={"search_disable": not False}
        )

    def num_tokens_from_messages(self, messages, model=None):
        """Return the number of tokens used by a list of messages. From https://github.com/DjangoPeng/openai-quickstart/blob/main/openai_api/count_tokens_with_tiktoken.ipynb"""
        # debug_logger.info(f"[debug] num_tokens_from_messages<model, self.model> = {model, self.model}")
        if model is None:
            model = "gpt-3.5-turbo-0613"
        # 尝试获取模型的编码
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # 如果模型没有找到，使用 cl100k_base 编码并给出警告
            debug_logger.info(f"Warning: {model} not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        # 针对不同的模型设置token数量
        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
            "gpt-4-32k",
            "gpt-4-1106-preview",
        }:
            tokens_per_message = 3
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4  # 每条消息遵循 {role/name}\n{content}\n 格式
            tokens_per_name = -1  # 如果有名字，角色会被省略
        elif "gpt-3.5-turbo" in model:
            # 对于 gpt-3.5-turbo 模型可能会有更新，此处返回假设为 gpt-3.5-turbo-0613 的token数量，并给出警告
            debug_logger.info(
                "Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            # 对于 gpt-4 模型可能会有更新，此处返回假设为 gpt-4-0613 的token数量，并给出警告
            debug_logger.info("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-4-0613")
        else:
            # 对于 其他 模型可能会有更新，此处返回假设为 gpt-3.5-turbo-1106 的token数量，并给出警告
            debug_logger.info(
                f"Warning: {model} may update over time. Returning num tokens assuming gpt-3.5-turbo-1106.")
            return self.num_tokens_from_messages(messages, model="gpt-3.5-turbo-1106")

        num_tokens = 0
        # 计算每条消息的token数
        for message in messages:
            if isinstance(message, dict):
                num_tokens += tokens_per_message
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
                    if key == "name":
                        num_tokens += tokens_per_name
            elif isinstance(message, str):
                num_tokens += len(encoding.encode(message))
            else:
                NotImplementedError(
                    f"""num_tokens_from_messages() is not implemented message type {type(message)}. """
                )

        num_tokens += 3  # 每条回复都以助手为首
        return num_tokens

    @property
    def _history_len(self) -> int:
        return self.history_len

    def set_history_len(self, history_len: int = 10) -> None:
        self.history_len = history_len

    async def generatorAnswer(self, prompt: str,
                              history: List[List[str]] = [],
                              streaming: bool = False) -> AnswerResult:

        if history is None or len(history) == 0:
            history = [[]]
        debug_logger.info(f"history_len: {self.history_len}")
        debug_logger.info(f"prompt: {prompt}")
        debug_logger.info(f"streaming: {streaming}")

        response = self._call(prompt, history[:-1], streaming)
        complete_answer = ""
        async for response_text in response:

            if response_text:
                complete_answer += response_text
            history[-1] = [prompt, complete_answer]
            answer_result = AnswerResult()
            answer_result.history = history
            answer_result.llm_output = {"answer": response_text}
            answer_result.prompt = prompt

            yield answer_result

    async def _call(self, prompt: str, history: List[List[str]], streaming: bool = False) -> str:
        messages = []
        for pair in history:
            question, answer = pair
            messages.append({"role": "user", "content": question})
            messages.append({"role": "assistant", "content": answer})
        messages.append({"role": "user", "content": prompt})
        debug_logger.info(messages)
        messages = [ChatMessage(role=msg['role'], content=msg['content']) for msg in messages]
        handler = AsyncChunkPrintHandler()
        a = self.client.astream(messages, config={"callbacks": [handler]})
        async for message in a:
            delta={'answer': message.content}
            # print("message:"+)
            yield "data: "+json.dumps(delta)

    def num_tokens_from_docs(self, docs):

        # 尝试获取模型的编码
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # 如果模型没有找到，使用 cl100k_base 编码并给出警告
            debug_logger.info("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")

        num_tokens = 0
        for doc in docs:
            num_tokens += len(encoding.encode(doc.page_content, disallowed_special=()))
        return num_tokens

async def main():
    llm = SparkApi()
    streaming = True
    chat_history = []
    prompt = "你是谁"
    result = llm.generatorAnswer(prompt=prompt,
                                 history=chat_history,
                                 streaming=streaming)
    async for i in result:
        print(i)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())

    # final_result = ""
    # for answer_result in llm.generatorAnswer(prompt=prompt,
    #                                          history=chat_history,
    #                                          streaming=streaming):
    #     resp = answer_result.llm_output["answer"]
    #     if "DONE" not in resp:
    #         final_result += json.loads(resp[6:])["answer"]
    #     debug_logger.info(resp)
    #
    # debug_logger.info(f"final_result = {final_result}")
