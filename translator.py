import json
import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"
LANGUAGES = ("en", "ja", "vi")

SYSTEM_PROMPT = (
    "You are a professional translator. Detect the source language and translate "
    "the user's text into English, Japanese, and Vietnamese. Keep the original meaning, "
    "tone, and line breaks. If the text is already in a target language, return it "
    "naturally polished in that language. Respond only in JSON: "
    '{"en": "...", "ja": "...", "vi": "..."}'
)


class TranslationError(Exception):
    """사용자에게 그대로 보여줄 수 있는 메시지를 담은 번역 오류."""


def get_api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY", "").strip() or None


def get_model() -> str:
    return os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL


def create_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def _parse(content: str | None) -> dict:
    data = json.loads(content or "")
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) for k in LANGUAGES):
        raise ValueError("missing language keys")
    return {k: data[k] for k in LANGUAGES}


def translate(client: OpenAI, text: str, model: str | None = None) -> dict:
    """text를 영어/일본어/베트남어로 번역해 {"en", "ja", "vi"}를 반환한다.

    응답 형식이 잘못되면 1회 재시도하고, 실패하면 TranslationError를 던진다.
    """
    model = model or get_model()
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
        except openai.AuthenticationError as e:
            raise TranslationError("API 키가 올바르지 않습니다.") from e
        except openai.RateLimitError as e:
            raise TranslationError("요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.") from e
        except openai.APIConnectionError as e:  # APITimeoutError 포함
            raise TranslationError("네트워크 연결을 확인하세요.") from e
        except openai.APIError as e:
            raise TranslationError("번역 서비스에서 오류가 발생했습니다. 잠시 후 다시 시도하세요.") from e

        try:
            return _parse(response.choices[0].message.content)
        except (ValueError, IndexError):
            if attempt == 1:
                raise TranslationError("번역 결과를 해석하지 못했습니다. 다시 시도하세요.")
