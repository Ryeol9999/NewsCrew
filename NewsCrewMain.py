from typing import Dict, Any, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# ==========================================
# 1. 상태(State) 정의
# ==========================================
class AgentState(TypedDict):
    keywords: str                # 사용자가 입력한 구독 키워드
    raw_data: str                # 리서치 에이전트가 수집한 원시 데이터
    draft: str                   # 작성 에이전트가 생성한 뉴스레터 초안
    review_feedback: str         # 검수 에이전트의 수정 요청 피드백
    review_status: Literal["APPROVED", "REJECTED"]  # 검수 통과 여부
    revision_count: int          # 무한 루프 방지를 위한 수정 횟수 카운트


# ==========================================
# 2. 툴 함수 (Mock Data 반환)
# ==========================================
def mock_search_tool(keywords: str) -> str:
    """웹 및 뉴스 API를 시뮬레이션하여 관련 원시 데이터를 반환하는 툴"""
    return f"[{keywords}] 관련 최신 트렌드 기사 핵심 내용 요약 데이터 (출처: Tavily/Google 뉴스 검색 API)"


# ==========================================
# 3. 노드(Node) 함수 정의
# ==========================================
def research_node(state: AgentState) -> Dict[str, Any]:
    print("\n[Node] 🔍 리서치 에이전트 가동")
    keywords = state.get("keywords", "")
    
    # 리서치 툴 호출 시뮬레이션
    search_result = mock_search_tool(keywords)
    
    return {"raw_data": search_result, "revision_count": 0}


def writer_node(state: AgentState) -> Dict[str, Any]:
    print("\n[Node] ✍️ 작성 에이전트 가동")
    raw_data = state.get("raw_data", "")
    feedback = state.get("review_feedback", "")
    count = state.get("revision_count", 0)
    
    # 자동 검수 에이전트로부터 피드백을 받았는지 확인
    if feedback:
        print(f" -> [수정 요청 반영] 피드백({feedback})에 따라 내용을 보완합니다. (수정 횟수: {count})")
        draft = (
            f"📰 [뉴스레터 최종본] 구독자님을 위한 맞춤형 테크 브리핑\n\n"
            f"지난 초안의 어조를 보완하고 가독성을 개선한 버전입니다.\n"
            f"수집된 정보: {raw_data}\n\n"
            f"감사합니다."
        )
    else:
        print(" -> [초안 작성] 수집된 원시 데이터를 바탕으로 뉴스레터 템플릿을 적용합니다.")
        draft = (
            f"📰 [뉴스레터 초안] 구독자님을 위한 맞춤형 테크 브리핑\n\n"
            f"안녕하세요! 오늘 가져온 핵심 소식입니다.\n"
            f"콘텐츠 내용: {raw_data}\n\n"
            f"의견이 있으시면 피드백을 남겨주세요."
        )
        
    return {"draft": draft}


def review_node(state: AgentState) -> Dict[str, Any]:
    print("\n[Node] 🛠️ 검수 에이전트 가동")
    count = state.get("revision_count", 0)
    
    # 핑퐁(무한 루프) 및 조건부 엣지 테스트를 위해 1회차에는 무조건 REJECTED를 반환하도록 시뮬레이션
    if count < 1:
        print(" -> [검수 결과] 품질 미달 판정: 전체적인 문체를 더 부드럽고 전문적으로 수정할 필요가 있습니다.")
        return {
            "review_status": "REJECTED",
            "review_feedback": "문체가 다소 딱딱합니다. 뉴스레터 톤앤매너에 맞게 친근하게 고쳐주세요.",
            "revision_count": count + 1
        }
    else:
        print(" -> [검수 결과] 품질 검증 통과 완료.")
        return {
            "review_status": "APPROVED",
            "review_feedback": "",
            "revision_count": count
        }


def send_newsletter_node(state: AgentState) -> Dict[str, Any]:
    """Human-in-the-loop 단계에서 '승인'을 받아 일시 정지가 풀린 후 최종 실행되는 노드"""
    print("\n[Node] 🚀 발송/저장 에이전트 가동")
    print("==================================================")
    print("최종 승인 완료! 사용자에게 이메일 발송 및 DB 저장을 수행합니다.")
    print(f"최종 발송 내용:\n{state.get('draft')}")
    print("==================================================")
    return {}


# ==========================================
# 4. 조건부 엣지(Conditional Edge) 함수 정의
# ==========================================
def should_continue(state: AgentState) -> Literal["rewrite", "human_approval"]:
    status = state.get("review_status")
    count = state.get("revision_count", 0)
    
    # 무한 루프 방지 안전장치
    if count >= 3:
        print("\n[System] 최대 수정 횟수 초과로 인해 강제로 승인 대기 단계로 진입합니다.")
        return "human_approval"
        
    if status == "REJECTED":
        return "rewrite"
    else:
        return "human_approval"


# ==========================================
# 5. 워크플로우 그래프 빌드 및 연결
# ==========================================
workflow = StateGraph(AgentState)

# 노드 등록
workflow.add_node("research_agent", research_node)
workflow.add_node("writer_agent", writer_node)
workflow.add_node("review_agent", review_node)
workflow.add_node("send_newsletter", send_newsletter_node)

# 기본 엣지 연결
workflow.add_edge(START, "research_agent")
workflow.add_edge("research_agent", "writer_agent")
workflow.add_edge("writer_agent", "review_agent")

# 조건부 엣지 추가: 검수 에이전트 평가에 따라 분기
workflow.add_conditional_edges(
    "review_agent",
    should_continue,
    {
        "rewrite": "writer_agent",          # 품질 미달 시 재작성으로 순환
        "human_approval": "send_newsletter" # 통과 시 발송 노드로 진행 (단, 인터럽트에 의해 진입 전 멈춤)
    }
)

workflow.add_edge("send_newsletter", END)

# 메모리 세이버 등록 및 멈출 지점(interrupt_before) 지정
#send_newsletter 실행 직전에 멈추어 Human-in-the-loop를 구현합니다.
memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["send_newsletter"])
#app = workflow.compile( interrupt_before=["send_newsletter"])


# ==========================================
# 6. 실행 및 흐름 테스트 시뮬레이션
# ==========================================
if __name__ == "__main__":
    # 대화를 식별할 가상의 고유 스레드 ID 생성
    config = {"configurable": {"thread_id": "newsletter_task_001"}}
    initial_input = {"keywords": "2026년 AI 트렌드 및 에이전트 산업"}
    
    print("=== [1단계] 에이전트 자동화 프로세스 시작 ===")
    print("설명: 리서치 -> 작성 -> 검수(반려) -> 재작성 -> 검수(통과) 후 발송 직전에서 멈춥니다.")
    
    # 그래프 실행 시작
    for event in app.stream(initial_input, config=config, stream_mode="values"):
        pass
        
    # ----------------------------------------------------
    # 이 시점에서 그래프는 interrupt_before 제한에 걸려 일시 중지됩니다.
    # FastAPI에서는 아래와 같이 대기 중인 상태의 State를 조회하여 사용자 인터페이스에 제공하게 됩니다.
    # ----------------------------------------------------
    print("\n=== [2단계] Human-in-the-loop 일시 중단 (FastAPI 대기 상태) ===")
    
    current_state = app.get_state(config)
    print(f"현재 워크플로우 대기 위치 (Next Node): {current_state.next}")
    print(f"생성 완료된 초안 미리보기:\n{current_state.values.get('draft')}")
    
    # ----------------------------------------------------
    # 사용자가 FastAPI 앱 웹화면에서 내용을 확인하고 '승인' 버튼을 누른 상황을 시뮬레이션합니다.
    # 실행을 재개할 때는 입력 값에 None을 주어 기존 State를 이어받아 멈춘 곳부터 다시 달립니다.
    # ----------------------------------------------------
    print("\n=== [3단계] FastAPI를 통해 사용자가 '승인'을 눌렀습니다. ===")
    print("설명: 대기 상태가 해제되며 최종 발송 노드가 처리됩니다.")
    
    for event in app.stream(None, config=config, stream_mode="values"):
        pass

    print("\n=== 프로세스 전체 종료 ===")