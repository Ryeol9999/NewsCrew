"""뉴스레터 파이프라인의 공유 상태(State) 정의."""
from __future__ import annotations

from typing import TypedDict


class ReviewResult(TypedDict):
    """검수 에이전트의 판정 결과."""
    passed: bool      # 품질 통과 여부
    score: int        # 0~100 점수
    feedback: str     # 수정 요청 사유 / 코멘트


class NewsletterState(TypedDict, total=False):
    """그래프 전체에서 공유되는 상태.

    [사용자 입력] -> [리서치] -> [작성] -> [검수] -> (조건부 복귀) -> [승인 대기] -> [발송]
    """
    keywords: list[str]        # 1. 사용자 입력: 관심 키워드
    research: str              # 2. 리서치 에이전트 결과
    draft: str                 # 3. 작성 에이전트 초안
    review: ReviewResult       # 4. 검수 에이전트 판정
    revision_count: int        # 작성<->검수 루프를 돈 횟수
    max_revisions: int         # 무한 루프 방지용 최대 재작성 횟수
    human_feedback: str        # 사람이 '반려' 시 남기는 추가 요청
    status: str                # researching | writing | reviewing | awaiting_approval | sent
    final: str                 # 6. 최종 발송 본문
