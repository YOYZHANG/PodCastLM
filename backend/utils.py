import asyncio
import glob
import io
import os
import re
import time
import hashlib
from typing import Any, Dict, Generator
import uuid
from openai import OpenAI
import requests
from fishaudio import fishaudio_tts
from prompts import LANGUAGE_MODIFIER, LENGTH_MODIFIERS, PODCAST_INFO_PROMPT, QUESTION_MODIFIER, SUMMARY_INFO_PROMPT, SYSTEM_PROMPT, TONE_MODIFIER
import json
from pydub import AudioSegment
from fastapi import UploadFile
from PyPDF2 import PdfReader
from schema import PodcastInfo, ShortDialogue, Summary
from constants import (
    AUDIO_CACHE_DIR,
    FIREWORKS_API_KEY,
    FIREWORKS_BASE_URL,
    FIREWORKS_MODEL_ID,
    FIREWORKS_MAX_TOKENS,
    FIREWORKS_TEMPERATURE,
    GRADIO_CLEAR_CACHE_OLDER_THAN,
    JINA_KEY,
    SPEECH_KEY,
    SPEECH_REGION,
)
import azure.cognitiveservices.speech as speechsdk

fw_client = OpenAI(base_url=FIREWORKS_BASE_URL, api_key=FIREWORKS_API_KEY)



def generate_dialogue(pdfFile, textInput, tone, duration, language) -> Generator[str, None, None]:
    modified_system_prompt = get_prompt(pdfFile, textInput, tone, duration, language)
    if (modified_system_prompt == False):
        yield json.dumps({
            "type": "error",
            "content": "Prompt is too long"
        }) + "\n"
        return
    full_response = ""
    llm_stream = call_llm_stream(SYSTEM_PROMPT, modified_system_prompt, ShortDialogue, isJSON=False)

    for chunk in llm_stream:
        yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
        full_response += chunk
        
    yield json.dumps({"type": "final", "content": full_response})

async def process_line(line, voice,provider):
    if provider == 'fishaudio':
        return await generate_podcast_audio(line['content'], voice)
    return await generate_podcast_audio_by_azure(line['content'], voice)

async def generate_podcast_audio_by_azure(text: str, voice: str) -> str:
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        speech_config.speech_synthesis_voice_name = voice

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        future =await asyncio.to_thread(synthesizer.speak_text_async, text)
        
        result = await asyncio.to_thread(future.get)

        print("Speech synthesis completed")

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Audio synthesized successfully")
            audio_data = result.audio_data
            audio_segment = AudioSegment.from_wav(io.BytesIO(audio_data))
            return audio_segment
        else:
            print(f"Speech synthesis failed: {result.reason}")
            if hasattr(result, 'cancellation_details'):
                print(f"Cancellation details: {result.cancellation_details.reason}")
                print(f"Cancellation error details: {result.cancellation_details.error_details}")
            return None

    except Exception as e:
        print(f"Error in generate_podcast_audio: {e}")
        raise

async def generate_podcast_audio(text: str, voice: str) -> str:
    return await generate_podcast_audio_by_fish(text,voice) 

async def generate_podcast_audio_by_fish(text: str, voice: str) -> str:
    try: 
        return fishaudio_tts(text=text,reference_id=voice)
    except Exception as e:
        print(f"Error in generate_podcast_audio: {e}")
        raise
async def process_lines_with_limit(lines, provider , host_voice, guest_voice, max_concurrency):
    semaphore = asyncio.Semaphore(max_concurrency)

    async def limited_process_line(line):
        async with semaphore:
            voice = host_voice if (line['speaker'] == '主持人' or line['speaker'] == 'Host') else guest_voice
            return await process_line(line, voice , provider)

    tasks = [limited_process_line(line) for line in lines]
    results = await asyncio.gather(*tasks)
    return results
async def combine_audio(task_status: Dict[str, Dict], task_id: str, text: str, language: str , provider:str,host_voice: str , guest_voice:str) -> Generator[str, None, None]:
    try:
        dialogue_regex = r'\*\*([\s\S]*?)\*\*[:：]\s*([\s\S]*?)(?=\*\*|$)'
        matches = re.findall(dialogue_regex, text, re.DOTALL)
        
        lines = [
        {
            "speaker": match[0],
            "content": match[1].strip(),
        }
        for match in matches
        ]

        print("Starting audio generation")
        # audio_segments = await asyncio.gather(
        #     *[process_line(line, host_voice if line['speaker'] == '主持人' else guest_voice) for line in lines]
        # )
        audio_segments = await process_lines_with_limit(lines,provider, host_voice, guest_voice, 10 if provider=='azure' else 5)
        print("Audio generation completed")

        # 合并音频
        combined_audio = await asyncio.to_thread(sum, audio_segments)

        print("Audio combined")

        # 只在最后写入文件
        unique_filename = f"{uuid.uuid4()}.mp3"

        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
        file_path = os.path.join(AUDIO_CACHE_DIR, unique_filename)
        
        # 异步导出音频文件
        await asyncio.to_thread(combined_audio.export, file_path, format="mp3")

        audio_url = f"/audio/{unique_filename}"
        task_status[task_id] = {"status": "completed", "audio_url": audio_url}

        for file in glob.glob(f"{AUDIO_CACHE_DIR}*.mp3"):
            if (
                os.path.isfile(file)
                and time.time() - os.path.getmtime(file) > GRADIO_CLEAR_CACHE_OLDER_THAN
            ):
                os.remove, file

        
        clear_pdf_cache()
        return audio_url
        
    except Exception as e:
        # 如果发生错误，更新状态为失败
        task_status[task_id] = {"status": "failed", "error": str(e)}


def generate_podcast_summary(pdf_content: str, text: str, tone: str, length: str, language: str) -> Generator[str, None, None]:
    modified_system_prompt = get_prompt(pdf_content, text, '', '', '')
    if (modified_system_prompt == False):
        yield json.dumps({
            "type": "error",
            "content": "Prompt is too long"
        }) + "\n"
        return
    stream = call_llm_stream(SUMMARY_INFO_PROMPT, modified_system_prompt, Summary, False)
    full_response = ""
    for chunk in stream:
        # 将每个 chunk 作为 JSON 字符串 yield
        yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
    
    yield json.dumps({"type": "final", "content": full_response})

def generate_podcast_info(pdfContent: str, text: str, tone: str, length: str, language: str) -> Generator[str, None, None]:
    modified_system_prompt = get_prompt(pdfContent, text, '', '', '')
    if (modified_system_prompt == False):
        yield json.dumps({
            "type": "error",
            "content": "Prompt is too long"
        }) + "\n"
        return

    full_response = ""
    for chunk in call_llm_stream(PODCAST_INFO_PROMPT, modified_system_prompt, PodcastInfo):
        full_response += chunk
    try:
        result = json.loads(full_response)
        
        yield json.dumps({
            "type": "podcast_info",
            "content": result
        }) + "\n"
    except Exception as e:
        yield json.dumps({
            "type": "error",
            "content": f"An unexpected error occurred: {str(e)}"
        }) + "\n"

def call_llm_stream(system_prompt: str, text: str, dialogue_format: Any, isJSON: bool = True) -> Generator[str, None, None]:
    """Call the LLM with the given prompt and dialogue format, returning a stream of responses."""
    request_params = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "model": FIREWORKS_MODEL_ID,
        "max_tokens": FIREWORKS_MAX_TOKENS,
        "temperature": FIREWORKS_TEMPERATURE,
        "stream": True  # 启用流式输出
    }

    # 如果需要 JSON 响应，添加 response_format 参数
    if isJSON:
        request_params["response_format"] = {
            "type": "json_object",
            "schema": dialogue_format.model_json_schema(),
        }
    stream = fw_client.chat.completions.create(**request_params)

    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            yield content

    # 在流结束时，尝试解析完整的 JSON 响应
    # try:
    #     parsed_response = json.loads(full_response)
    #     yield json.dumps({"type": "final", "content": parsed_response})
    # except json.JSONDecodeError:
    #     yield json.dumps({"type": "error", "content": "Failed to parse JSON response"})

def call_llm(system_prompt: str, text: str, dialogue_format: Any) -> Any:
    """Call the LLM with the given prompt and dialogue format."""
    response = fw_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        model=FIREWORKS_MODEL_ID,
        max_tokens=FIREWORKS_MAX_TOKENS,
        temperature=FIREWORKS_TEMPERATURE,
        response_format={
            "type": "json_object",
            "schema": dialogue_format.model_json_schema(),
        },
    )
    return response

pdf_cache = {}
def clear_pdf_cache():
    global pdf_cache
    pdf_cache.clear()

def get_link_text(url: str):
    """ 通过jina.ai 抓取url内容 """
    url  = f"https://r.jina.ai/{url}"
    headers = {}
    headers['Authorization'] = 'Bearer ' + JINA_KEY
    headers['Accept'] = 'application/json'
    headers['X-Return-Format'] = 'text'
    response = requests.get(url, headers=headers)
    return response.json()['data']

async def get_pdf_text(pdf_file: UploadFile):
    text = ""
    print(pdf_file)
    try:
       # 读取上传文件的内容
        contents = await pdf_file.read()
        file_hash = hashlib.md5(contents).hexdigest()

        if file_hash in pdf_cache:
            return pdf_cache[file_hash]
        
        # 使用 BytesIO 创建一个内存中的文件对象
        pdf_file_obj = io.BytesIO(contents)
        
        # 使用 PdfReader 读取 PDF 内容
        pdf_reader = PdfReader(pdf_file_obj)
        
        # 提取所有页面的文本
        text = "\n\n".join([page.extract_text() for page in pdf_reader.pages])
        
        # 重置文件指针，以防后续还需要读取文件
        await pdf_file.seek(0)

        return text

    except Exception as e:
        return {"error": str(e)}

def get_prompt(pdfContent: str, text: str, tone: str, length: str, language: str):
    modified_system_prompt = ""
    new_text = pdfContent +text
    if pdfContent:
        modified_system_prompt += f"\n\n{QUESTION_MODIFIER} {new_text}"
    if tone:
        modified_system_prompt += f"\n\n{TONE_MODIFIER} {tone}."
    if length:
        modified_system_prompt += f"\n\n{LENGTH_MODIFIERS[length]}"
    if language:
        modified_system_prompt += f"\n\n{LANGUAGE_MODIFIER} {language}."

    return modified_system_prompt
