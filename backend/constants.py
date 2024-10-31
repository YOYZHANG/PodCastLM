"""
constants.py
"""

import os

from pathlib import Path

# Key constants
CHARACTER_LIMIT = 100_000

# Gradio-related constants
GRADIO_CLEAR_CACHE_OLDER_THAN = 1 * 2 * 60 * 60  # 2 hours

AUDIO_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'tmp', 'cache')

# Error messages-related constants
ERROR_MESSAGE_NO_INPUT = "Please provide at least one PDF file or a URL."
ERROR_MESSAGE_NOT_PDF = "The provided file is not a PDF. Please upload only PDF files."
ERROR_MESSAGE_NOT_SUPPORTED_IN_MELO_TTS = "The selected language is not supported without advanced audio generation. Please enable advanced audio generation or choose a supported language."
ERROR_MESSAGE_READING_PDF = "Error reading the PDF file"
ERROR_MESSAGE_TOO_LONG = "The total content is too long. Please ensure the combined text from PDFs and URL is fewer than {CHARACTER_LIMIT} characters."

SPEECH_KEY = os.getenv('SPEECH_KEY')
SPEECH_REGION = "japaneast"

FISHAUDIO_KEY = os.getenv('FISHAUDIO_KEY')
JINA_KEY = os.getenv('JINA_KEY','jina_c1759c7f49e14ced990ac7776800dc44ShJNTXBCizzwjE7IMFYJ6LD960cG')

# Fireworks API-related constants
FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY')
FIREWORKS_BASE_URL = os.getenv('FIREWORKS_BASE_URL',"https://api.fireworks.ai/inference/v1")
FIREWORKS_MAX_TOKENS = 16_384
FIREWORKS_MODEL_ID = os.getenv('FIREWORKS_MODEL_ID',"accounts/fireworks/models/llama-v3p1-405b-instruct")
FIREWORKS_TEMPERATURE = 0.1
FIREWORKS_JSON_RETRY_ATTEMPTS = 3
# Suno related constants
SUNO_LANGUAGE_MAPPING = {
    "English": "en",
    "Chinese": "zh",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Turkish": "tr",
}


FISHAUDIO_SPEEKER = [
    { "id": "59cb5986671546eaa6ca8ae6f29f6d22", "name": "央视配音" },
    { "id": "738d0cc1a3e9430a9de2b544a466a7fc", "name": "雷军" },
    { "id": "54a5170264694bfc8e9ad98df7bd89c3", "name": "丁真" },
    { "id": "7f92f8afb8ec43bf81429cc1c9199cb1", "name": "AD学姐" },
    { "id": "0eb38bc974e1459facca38b359e13511", "name": "赛马娘" },
    { "id": "e80ea225770f42f79d50aa98be3cedfc", "name": "孙笑川258" },
    { "id": "e4642e5edccd4d9ab61a69e82d4f8a14", "name": "蔡徐坤" },
    { "id": "f7561ff309bd4040a59f1e600f4f4338", "name": "黑手" },
    { "id": "332941d1360c48949f1b4e0cabf912cd", "name": "丁真（锐刻五代版）" },
    { "id": "1aacaeb1b840436391b835fd5513f4c4", "name": "芙宁娜" },
    { "id": "3b55b3d84d2f453a98d8ca9bb24182d6", "name": "邓紫琪" },
    { "id": "7af4d620be1c4c6686132f21940d51c5", "name": "东雪莲" },
    { "id": "e1cfccf59a1c4492b5f51c7c62a8abd2", "name": "永雏塔菲" },
    { "id": "665e031efe27435780ebfa56cc7e0e0d", "name": "月半猫" },
    { "id": "aebaa2305aa2452fbdc8f41eec852a79", "name": "雷军" },
    { "id": "7c66db6e457c4d53b1fe428a8c547953", "name": "郭德纲" },
    { "id": "99503144194c45ed8fb998ceac181dcc", "name": "贝利亚" },
    { "id": "4462fa28f3824bff808a94a6075570e5", "name": "雷军" },
    { "id": "188c9b7c06654042be0e8a25781761e8", "name": "周杰伦" },
    { "id": "6ce7ea8ada884bf3889fa7c7fb206691", "name": "御女茉莉" }
]
SPEEKERS = {
    "fishaudio":FISHAUDIO_SPEEKER,
    "azure":[
        {"id":"zh-CN-YunxiNeural","name":"云希"},
        {"id":"zh-CN-YunzeNeural","name":"云哲"},
        {"id":"zh-CN-YunxuanNeural","name":"晓萱"},
    ]
}
