import os, re, json, ast
from dotenv import load_dotenv
from openai import OpenAI
from .logger import logger
from . import tags as _tags_mod


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

def _chat(messages: list[dict]) -> str:
    res = client.chat.completions.create(model=MODEL, messages=messages)
    return res.choices[0].message.content

def refine_news(article: str) -> str:
    system = (
      "당신은 데이터를 정제하는 일을 수행합니다.\n"
      "입력으로 들어오는 데이터는 뉴스 기사를 크롤링한 문자열 배열 데이터입니다.\n"
      "배열에 포함된 문자열 중 뉴스 내용과 관련없는 출처나 저작권 정보, 기자 정보와 같은 내용을 포함한 문자열은 삭제해야합니다.\n"
      "~기자입니다. ㅇㅇ뉴스 ㅇㅇ입니다. 같은 내용의 문자열도 삭제합니다."
      "문자열의 내용을 수정해서는 안되며 삭제만 가능합니다.\n"
      "내용과 관련없는 문자열을 삭제한 뒤에는 모든 문자열을 하나의 문자열로 병합합니다.\n"
      "결과는 하나의 문자열로 리턴합니다."
  )
    return _chat([{"role":"system","content":system},
                  {"role":"user","content":article}])

def _extract_json(text: str) -> str | None:
    # ```json ...``` 또는 ```...``` 블록 처리
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # JSON 객체 {}를 가장 먼저 발견한 위치에서 반환
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        return match.group(0).strip()

    # JSON 배열 []를 가장 먼저 발견한 위치에서 반환
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if match:
        return match.group(0).strip()

    return None




def mk_TTS_prompt(cleaned: str) -> tuple[list[str], list[str]]:
    system = (
        "당신은 뉴스 기사를 두 가지 버전으로 요약하는 전문가입니다.\n"
        "다음 지시사항을 정확히 지켜서 결과를 생성하세요:\n\n"
        "1. 요약은 반드시 두 가지 말투로 작성하며, 각각 정확히 5문장씩입니다.\n"
        "2. 각 문장의 길이는 약 60자 내외이며 간결하고 명확해야 합니다.\n\n"
        "- 첫 번째 요약본 (키: 'formal'): 아나운서가 뉴스 읽듯 '-입니다' 말투를 사용합니다.\n"
        "- 두 번째 요약본 (키: 'casual'): 친근하고 장난스러운 말투를 사용합니다.\n\n"
        "반드시 다음과 같은 JSON 형식으로만 결과를 반환합니다:\n"
        "{\n"
        "  \"formal\": [\"-입니다 말투 문장1\", ..., \"-입니다 말투 문장5\"],\n"
        "  \"casual\": [\"친근한 말투 문장1\", ..., \"친근한 말투 문장5\"]\n"
        "}\n\n"
        "다른 형식의 응답이나 추가 설명은 절대 하지 마세요."
    )


    raw = _chat([{"role": "system", "content": system}, {"role": "user", "content": cleaned}])
    logger.debug(f"[TTS_RAW] {raw}")

    json_str = _extract_json(raw) or raw
    json_str = json_str.replace("'", '"')

    try:
        parsed = json.loads(json_str)

        if isinstance(parsed, dict) and "formal" in parsed and "casual" in parsed:
            return parsed["formal"], parsed["casual"]
        else:
            raise ValueError(f"잘못된 JSON 구조: {parsed}")

    except Exception as e:
        logger.error(f"Invalid JSON parsing: {e}, RAW: {raw}")
        raise ValueError(f"JSON 파싱 실패: {e}") from e



def mk_TTV_prompt(formal: list[str]) -> list[str]:
    system = (
    "You are a content generator for a text-to-video application. Your task is to create simple English sentences\n"
    "that describe a visible scene. Each sentence must:\n"
    "- Include a clear subject (e.g., a person, an object, or an animal).\n"
    "- If the subject is a human, use 'a man' or 'a woman' unless it is a child.\n"
    "- Optionally mention clothing (e.g., 'a man in a blue shirt').\n"
    "- Describe only one or two people per sentence.\n"
    "- Use a clear action verb (e.g., 'run,' 'jump,' 'write').\n"
    "- Avoid abstract verbs or concepts that cannot be easily visualized.\n"
    "- Include a location (e.g., 'on the street,' 'in the park').\n"
    "- Do not use proper nouns (e.g., names of people, places, or organizations).\n"
    "- Use only common and simple words.\n"
    "\nExample sentences:\n"
    "- A man runs on the street.\n"
    "- A dog jumps in the park.\n"
    "- A woman writes at a desk.\n"
    "\nPlease respond with strictly valid JSON only.\n"
    "Your output must be a JSON array of exactly five English sentences.\n"
    "Do not include any markdown, code fences, comments, or extra fields.\n"
    "Ensure the response parses with json.loads() without errors.\n"
    "Example output: ["
        "\"A man runs on the street.\", "
        "\"A dog jumps in the park.\", "
        "\"A child reads a book in a library.\", "
        "\"A dog jumps over a puddle on a street.\", "
        "\"A chef cooks pasta in a kitchen.\""
    "]\n"
    )

    raw = _chat([{"role":"system","content":system},
                 {"role":"user","content":" ".join(formal)}])
    logger.info(f"TTV raw output -> {raw}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"TTV parse error: {e}. raw was: {raw!r}")
        # fallback: 빈 리스트 또는 prompt 그대로 리턴
        return []
    return parsed

def mk_tags(summary: str) -> list[str]:
    """요약문에서 태그 4개 추출"""
    print("tag 산출 완료")
    return _tags_mod.generate(summary)