"""knowledge/llm_client.py — Claude API 호출 공통 래퍼.

gate1/gate2/extract_claims이 겪은 문제(빈 응답 → JSONDecodeError가 "API 오류"로
뭉개져 원인 불명인 채 개별 문서 단위로 계속 반복 소모)를 해결하기 위해:
1. 짧은 재시도(네트워크 flakiness 대응)
2. 실패 시 원인을 식별 가능한 형태로 노출 (상태 코드/예외 타입)
3. 같은 원인의 실패가 연속되면 개별 문서를 계속 태우는 대신 즉시 중단(circuit breaker)
"""
from __future__ import annotations

import json
import time

import anthropic

_CLIENT = anthropic.Anthropic()


class LLMCallError(Exception):
    """진단 가능한 형태로 감싼 API 호출 실패."""


def _diagnose(e: Exception) -> str:
    if isinstance(e, anthropic.APIStatusError):
        return f"{type(e).__name__} status={e.status_code} body={str(e.body)[:200]}"
    if isinstance(e, anthropic.APIConnectionError):
        return f"{type(e).__name__} (네트워크/연결 실패): {e}"
    if isinstance(e, json.JSONDecodeError):
        return f"{type(e).__name__} (응답이 JSON이 아님, 빈 바디 가능성): {e}"
    return f"{type(e).__name__}: {e}"


def call_json(model: str, system: str, user_content: str, max_tokens: int, retries: int = 2) -> dict | list:
    """Claude에 호출 후 JSON으로 파싱. 실패 시 LLMCallError(진단 메시지 포함)."""
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            msg = _CLIENT.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            text = msg.content[0].text
            return json.loads(text)
        except Exception as e:  # noqa: BLE001 — 의도적으로 광범위 포착 후 재진단
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
                f"마지막 오류: {self._last_msg} (ANTHROPIC_API_KEY / 네트워크 확인 필요)"
            )
