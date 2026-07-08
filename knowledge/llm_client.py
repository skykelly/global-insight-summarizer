"""knowledge/llm_client.py — OpenAI API 호출 공통 래퍼.

파이프라인 전체의 LLM 호출을 한 곳으로 모은다(공급자 단일화).
- call_json: JSON 응답 파싱 (gate1/gate2/extract_claims)
- call_text: 원문 텍스트 응답 (summarize/generate_wiki 등)

빈 응답 → JSONDecodeError가 "API 오류"로 뭉개져 원인 불명인 채 개별 문서
단위로 계속 소모되던 문제를 방지하기 위해:
1. 짧은 재시도(네트워크 flakiness 대응)
2. 실패 원인을 식별 가능한 형태로 노출 (상태 코드/예외 타입)
3. 같은 원인의 실패가 연속되면 즉시 중단(circuit breaker)

모델은 env로 오버라이드 가능:
  OPENAI_MODEL_FILTER (기본 gpt-4o-mini) — 관련성 필터/스코어링(구 Haiku 역할)
  OPENAI_MODEL_MAIN   (기본 gpt-4o)      — 추출·요약·wiki 생성(구 Sonnet 역할)
"""
from __future__ import annotations

import json
import os
import time

import openai
from openai import OpenAI

# 비용 계층화 — 필요 시 env로 gpt-4.1-mini 등으로 교체
MODEL_FILTER = os.environ.get("OPENAI_MODEL_FILTER", "gpt-4o-mini")
MODEL_MAIN = os.environ.get("OPENAI_MODEL_MAIN", "gpt-4o")

# OpenAI 클라이언트는 키가 없으면 생성 시점에 예외를 던진다.
# 모듈 임포트만으로 실패하지 않도록(테스트·빌드 대비) 첫 사용까지 생성을 지연한다.
_CLIENT: OpenAI | None = None


def _client() -> OpenAI:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenAI()
    return _CLIENT


class LLMCallError(Exception):
    """진단 가능한 형태로 감싼 API 호출 실패."""


def _diagnose(e: Exception) -> str:
    if isinstance(e, openai.APIStatusError):
        return f"{type(e).__name__} status={e.status_code} body={str(getattr(e, 'body', ''))[:200]}"
    if isinstance(e, openai.APIConnectionError):
        return f"{type(e).__name__} (네트워크/연결 실패): {e}"
    if isinstance(e, json.JSONDecodeError):
        return f"{type(e).__name__} (응답이 JSON이 아님, 빈 바디 가능성): {e}"
    return f"{type(e).__name__}: {e}"


def _chat(model: str, system: str, user_content: str, max_tokens: int, json_mode: bool) -> str:
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }
    if json_mode:
        # response_format=json_object 는 프롬프트에 "json" 언급을 요구한다(시스템 프롬프트에 포함됨).
        kwargs["response_format"] = {"type": "json_object"}
    resp = _client().chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def call_json(model: str, system: str, user_content: str, max_tokens: int, retries: int = 2) -> dict | list:
    """OpenAI 호출 후 JSON으로 파싱. 실패 시 LLMCallError(진단 메시지 포함).

    ※ response_format=json_object 는 최상위가 객체여야 한다. 배열이 필요한 호출부
      (extract_claims)는 {"claims": [...]} 형태로 감싸서 요청하고 언랩한다.
    """
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            text = _chat(model, system, user_content, max_tokens, json_mode=True)
            return json.loads(text)
        except Exception as e:  # noqa: BLE001 — 의도적으로 광범위 포착 후 재진단
            last_err = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise LLMCallError(_diagnose(last_err)) from last_err


def call_text(model: str, system: str, user_content: str, max_tokens: int, retries: int = 2) -> str:
    """OpenAI 호출 후 원문 텍스트 반환(요약·wiki 등 마크다운). 실패 시 LLMCallError."""
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return _chat(model, system, user_content, max_tokens, json_mode=False)
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise LLMCallError(_diagnose(last_err)) from last_err


class CircuitBreaker:
    """연속 N회 실패 시 중단 — 시스템 장애 시 큐 전체를 헛돌지 않기 위함."""

    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self._consecutive = 0
        self._last_msg = ""

    def record_success(self) -> None:
        self._consecutive = 0

    def record_failure(self, msg: str) -> None:
        self._consecutive += 1
        self._last_msg = msg
        if self._consecutive >= self.threshold:
            raise RuntimeError(
                f"연속 {self._consecutive}회 동일 계열 실패로 중단 — 시스템 장애로 판단. "
                f"마지막 오류: {self._last_msg} (OPENAI_API_KEY / 네트워크 확인 필요)"
            )
