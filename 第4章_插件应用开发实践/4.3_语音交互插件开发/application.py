import os

from iat_ws_python3 import ASR
from tts_ws_python3 import TTS
from iflytek_spark_api import *
import recording


if __name__ == "__main__":
    import config
    # 加载api密钥以及星火模型的配置
    apiKey = config.acount_info["apiKey"]
    appId = config.acount_info["appId"]
    apiSecret = config.acount_info["apiSecret"]

    spark_requestUrl = config.SPARK_settings["spark_url"]
    spark_domain=config.SPARK_settings['domain']

    audio_path = 'data/cache/record_cache.pcm'

    print("-*-spark demo-*-")
    # 录音功能初始化
    AR = recording.AudioRecord()

    flag = input("Enter键开启语音交互，数字或字母键退出~")
    while flag == '':
        # 开始录音
        AR.record_audio(audio_cache_path=audio_path)

        print("语音识别中......")
        # 语音识别
        asr = ASR(appId, apiSecret,apiKey,audio_path)
        asr.start_send()
        query = asr.get_response()
        os.remove(audio_path)
        print("我:", query)

        # 星火问答
        question = checklen(getText("user", query))
        print("星火:", end="")
        spark_answer = get_spark_answer(appId, apiKey, apiSecret, spark_requestUrl, spark_domain ,question)
        print(spark_answer)

        # 语音合成
        print("\n语音合成中......")
        tts = TTS(appId, apiSecret,apiKey,spark_answer)
        tts.start_send()
        # 播放回答
        tts.playmp3()
        flag = input("Enter键开启语音交互，数字或字母键退出~")

    print("退出程序")


