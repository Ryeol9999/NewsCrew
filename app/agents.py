"""각 단계를 담당하는 에이전트(노드) 구현.

OPENAI_API_KEY 가 없으면 자동으로 Mock 모드로 동작하여
API 키 없이도 전체 파이프라인을 데모할 수 있습니다.
"""
from __future__ import annotations

import os
import re

from dotenv import load_dotenv

from .state import NewsletterState, ReviewResult

load_dotenv()

_USE_MOCK = not os.getenv("OPENAI_API_KEY")


def _get_llm():
    """ChatOpenAI 인스턴스 반환 (Mock 모드면 None)."""
    if _USE_MOCK:
        return None
    from langchain_openai import ChatOpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=0.7)


def _chat(system: str, user: str) -> str:
    """LLM 호출 헬퍼. Mock 모드면 간단한 더미 텍스트를 반환."""
    llm = _get_llm()
    if llm is None:
        return f"[MOCK]\n{user[:500]}"
    from langchain_core.messages import HumanMessage, SystemMessage

    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return resp.content


# ==========================================================================
# STEP 2. 리서치 에이전트 - 관련 자료 수집·정리
# ==========================================================================
def research_node(state: NewsletterState) -> NewsletterState:
    keywords = state.get("keywords", [])
    kw = ", ".join(keywords)
    print(f"[리서치] 키워드 조사 중: {kw}")

    if _USE_MOCK:
        research = (
            f"'{kw}' 관련 핵심 동향 3가지(Mock):\n"
            f"1. {keywords[0] if keywords else '주제'} 시장이 빠르게 성장하고 있습니다.\n"
            f"2. 신규 기술/서비스가 연이어 출시되고 있습니다.\n"
            f"3. 사용자 관심도가 전년 대비 크게 증가했습니다."
        )
    else:
        research = _chat(
            system="당신은 리서치 에이전트입니다. 주어진 키워드에 대한 최신 동향과 핵심 사실을 "
                   "간결한 불릿 포인트로 정리합니다.",
            user=f"다음 키워드에 대한 뉴스레터용 리서치 자료를 정리해 주세요: {kw}",
        )

    return {"research": research, "status": "writing"}


# ==========================================================================
# STEP 3. 작성 에이전트 - 초안 작성·구성
# ==========================================================================
def write_node(state: NewsletterState) -> NewsletterState:
    research = state.get("research", "")
    revision = state.get("revision_count", 0)
    feedback = ""
    # 검수 반려 또는 사람 반려 시 피드백을 반영
    if state.get("review") and not state["review"].get("passed", True):
        feedback = state["review"].get("feedback", "")
    if state.get("human_feedback"):
        feedback = state["human_feedback"]

    print(f"[작성] 초안 작성 중 (수정 {revision}회차) "
          f"{'/ 피드백 반영: ' + feedback if feedback else ''}")

    if _USE_MOCK:
        draft = (
            f"# 이번 주 뉴스레터\n\n"
            f"안녕하세요! 관심 키워드 기반 맞춤 뉴스레터입니다.\n\n"
            f"## 주요 소식\n{research}\n\n"
            f"## 마무리\n다음 호에서 더 알찬 소식으로 찾아뵙겠습니다."
        )
        if feedback:
            draft += f"\n\n> (수정 반영: {feedback})"
        # Mock 환경에서 1회차 초안은 일부러 품질 미달로 만들어 복귀 루프를 시연
        if revision == 0 and not feedback:
            draft = "# 뉴스레터\n\n소식입니다.\n"  # 너무 짧음 -> 검수 탈락
    else:
        instruction = "당신은 뉴스레터 작성 에이전트입니다. 리서치 자료를 바탕으로 친근하고 " \
                      "읽기 쉬운 뉴스레터 초안을 마크다운으로 작성합니다."
        if feedback:
            instruction += f" 다음 수정 요청을 반드시 반영하세요: {feedback}"
        draft = _chat(system=instruction, user=f"리서치 자료:\n{research}")

    return {"draft": draft, "status": "reviewing"}


# ==========================================================================
# STEP 4. 검수 에이전트 - 품질·사실 검증 (Conditional Edge 의 판정 주체)
# ==========================================================================
def review_node(state: NewsletterState) -> NewsletterState:
    draft = state.get("draft", "")
    revision = state.get("revision_count", 0)
    print(f"[검수] 초안 품질 검증 중 (수정 {revision}회차)")

    if _USE_MOCK:
        # 간단한 규칙 기반 검수: 길이/구성 확인
        length_ok = len(draft) > 80
        has_section = "##" in draft
        passed = length_ok and has_section
        score = 90 if passed else 40
        if passed:
            feedback = "구성과 분량이 적절합니다. 통과."
        else:
            reasons = []
            if not length_ok:
                reasons.append("내용이 너무 짧습니다")
            if not has_section:
                reasons.append("섹션 구성이 부족합니다")
            feedback = "품질 미달: " + ", ".join(reasons) + ". 보강이 필요합니다."
        review: ReviewResult = {"passed": passed, "score": score, "feedback": feedback}
    else:
        verdict = _chat(
            system="당신은 엄격한 검수 에이전트입니다. 뉴스레터 초안을 평가하여 정확히 다음 형식으로만 "
                   "답하세요:\nSCORE: <0-100 정수>\nPASS: <yes 또는 no>\nFEEDBACK: <한 줄 사유>",
            user=f"다음 초안을 검수하세요:\n{draft}",
        )
        score_m = re.search(r"SCORE:\s*(\d+)", verdict)
        pass_m = re.search(r"PASS:\s*(yes|no)", verdict, re.IGNORECASE)
        fb_m = re.search(r"FEEDBACK:\s*(.+)", verdict)
        score = int(score_m.group(1)) if score_m else 0
        passed = bool(pass_m and pass_m.group(1).lower() == "yes")
        feedback = fb_m.group(1).strip() if fb_m else verdict
        review = {"passed": passed, "score": score, "feedback": feedback}

    print(f"[검수] 결과: {'통과' if review['passed'] else '미달'} (점수 {review['score']})")
    return {
        "review": review,
        "revision_count": revision + 1,
        "status": "awaiting_approval" if review["passed"] else "writing",
        "human_feedback": "",  # 피드백 1회 소비
    }


# ==========================================================================
# STEP 6. 발송·저장 (사람 승인 이후 실행됨)
# ==========================================================================
def send_node(state: NewsletterState) -> NewsletterState:
    draft = state.get("draft", "")
    print("[발송] 사람 승인 완료 -> 뉴스레터 발송 및 이력 저장")
    # 실제 환경에서는 여기서 이메일 발송(AWS SES 등) + DB 저장 수행
    return {"final": draft, "status": "sent"}
