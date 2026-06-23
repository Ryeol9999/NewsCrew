"""LangGraph 그래프 구성.

핵심 기능
- Conditional Edges : 검수(review)가 '품질 미달'이면 작성(write)으로 복귀하는 순환 구조
- Human-in-the-loop : send 노드 직전에서 interrupt_before 로 실행을 일시 중단
"""
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .agents import research_node, review_node, send_node, write_node
from .state import NewsletterState


def _route_after_review(state: NewsletterState) -> str:
    """검수 결과에 따른 분기.

    - 통과            -> send (이후 interrupt_before 로 승인 대기)
    - 미달 & 재시도 가능 -> write (작성 단계로 복귀)
    - 미달 & 한도 초과   -> send (한도 초과 시 사람이 직접 판단하도록 승인 대기로 보냄)
    """
    review = state.get("review", {})
    revision = state.get("revision_count", 0)
    max_rev = state.get("max_revisions", 2)

    if review.get("passed"):
        return "send"
    if revision < max_rev:
        return "write"  # 품질 미달 -> 작성 단계로 복귀 (수정 요청)
    return "send"  # 최대 횟수 초과 -> 사람이 최종 판단


def build_graph():
    """체크포인터와 interrupt_before 가 적용된 컴파일된 그래프 반환."""
    builder = StateGraph(NewsletterState)

    builder.add_node("research", research_node)
    builder.add_node("write", write_node)
    builder.add_node("review", review_node)
    builder.add_node("send", send_node)

    builder.add_edge(START, "research")
    builder.add_edge("research", "write")
    builder.add_edge("write", "review")

    # Conditional Edge: 검수 결과로 분기 (복귀 루프의 핵심)
    builder.add_conditional_edges(
        "review",
        _route_after_review,
        {"write": "write", "send": "send"},
    )
    builder.add_edge("send", END)

    # MemorySaver 체크포인터 + send 직전 인터럽트 => Human-in-the-loop
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer, interrupt_before=["send"])


# 앱 전역에서 공유하는 단일 그래프 인스턴스
graph = build_graph()
