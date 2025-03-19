import re
from typing import List, Optional, Type
import openai
from pydantic import BaseModel

from config import (
    LLM_API_KEY,
    LLM_ENDPOINT,
    model_name,    
    max_tokens,
    temperature,
    temperature_structured,
)
from utils.logging_config import setup_logging
from utils.singleton import singleton



@singleton
class LLMService:
    """
       Singleton class for managing interactions with the Language Model (LLM).
       This class handles the initialization of the LLM client and provides methods
       for generating text and structured data based on prompts.
    """
    def __init__(self):
        if not LLM_API_KEY or not LLM_ENDPOINT:
            raise ValueError("LLM_API_KEY/LLM_ENDPOINT environment variable not set")
        self.client = openai.OpenAI(api_key=LLM_API_KEY, base_url=LLM_ENDPOINT)
        self.logger = setup_logging('LLMService')


    def _has_chinese(self, text: str) -> bool:
        return bool(re.search(u'[\u4e00-\u9fff]', text))


    def _generate_completion(self, messages: List[dict], schema: Optional[Type[BaseModel]] = None):
        params = {
            "model": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if schema:
            params.update({
                "response_format": schema,
                "extra_body": {"guided_decoding_backend": "outlines"},
                "temperature": temperature_structured,
            })

        for _ in range(3):
            completion = self.client.beta.chat.completions.parse(**params)
            if not schema:
                result = completion.choices[0].message.content
                if not self._has_chinese(result):
                    return result
            else:
                result = completion.choices[0].message.parsed
                if not any([self._has_chinese(elem) for elem in list(result)[0][-1]]):
                    return result
            self.logger.warning(f"Response contains chinese symbols, trying again")
        return result


    def generate_text(self, prompt: str, message: str) -> str:
        self.logger.info("Processing text generation request")
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ]
        result = self._generate_completion(messages)
        self._log_result(result, message)
        return result


    def generate_structured(self, prompt: str, message: str, schema: Type[BaseModel]):
        self.logger.info("Processing structured generation request")
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ]
        result = self._generate_completion(messages, schema)
        self._log_result(result, message, schema=schema)
        return result


    def _log_result(self, result: any, message: str, schema: Optional[Type[BaseModel]] = None):
        if result:
            self.logger.info("Response received successfully")
        else:
            log_msg = f"Empty response for message: {message}"
            if schema:
                log_msg += f", schema: {schema.__name__}"
            self.logger.warning(log_msg)
