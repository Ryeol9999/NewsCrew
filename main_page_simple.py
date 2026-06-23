"""맞춤형 뉴스레터 에이전트 — 학습용 심플 버전 (뼈대 + 빈칸).

이 파일은 초보자가 코드를 한 눈에 이해하고, 복잡한 부분은 직접
채워 넣으며 공부할 수 있도록 만든 "뼈대(skeleton)" 입니다.

  - 기능마다 함수 1개로 나눠 놓았습니다. (위에서 아래로 읽으면 흐름이 보입니다)
  - 복잡한 로직은 비워 두고  # TODO: 여기 채우기  주석을 달았습니다.
  - 빈칸은 지금도 "가짜 임시 결과"를 돌려주므로, 채우기 전에도
    실행하면 화면이 정상 동작합니다.

실행 방법:
    streamlit run main_page_simple.py

다 만든 정식 버전이 궁금하면 옆 파일 main_page.py 를 참고하세요.
"""
from __future__ import annotations

import uuid                      # 매번 다른 ID(thread_id) 만들 때 사용
from datetime import datetime    # 현재 시각/날짜

import streamlit as st


# ==========================================================================
# 1) 페이지 기본 설정 + 화면 꾸미기(CSS)
#    - 화면 제목, 아이콘, 레이아웃을 정합니다.
#    - 색/모양을 바꾸고 싶으면 inject_css() 안의 CSS만 고치면 됩니다.
# ==========================================================================
def setup_page():
    st.set_page_config(
        page_title="뉴스레터 에이전트 (학습용)",
        page_icon="📰",
        layout="centered",   # 가운데 정렬. 넓게 쓰려면 "wide"
    )


def inject_css():
    # 채팅 말풍선 정도만 간단히 꾸밉니다. (복잡한 디자인은 일부러 뺐습니다)
    st.markdown(
        """
        <style>
        .msg      { padding:10px 14px; border-radius:12px; margin:6px 0;
                    max-width:80%; line-height:1.5; }
        .msg.user { background:#5681d0; color:#fff; margin-left:auto; }  /* 내 말 */
        .msg.bot  { background:#2a2a40; color:#eee; }                    /* AI 말  */
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================================
# 2) 세션 상태 초기화
#    - Streamlit 은 화면을 새로 그릴 때마다 코드를 처음부터 다시 실행합니다.
#    - 그래도 값이 유지되도록 st.session_state 라는 "기억 상자"에 담아 둡니다.
#    - setdefault: 값이 없을 때만 처음 한 번 넣어 줍니다.
# ==========================================================================
def init_state():
    ss = st.session_state
    ss.setdefault("messages", [                       # 채팅 기록
        {"role": "assistant", "content": "안녕하세요! 어떤 주제의 뉴스레터를 원하세요? 🙂"},
    ])
    ss.setdefault("thread_id", None)                  # 현재 작업 ID
    ss.setdefault("snap", None)                        # AI가 만든 결과(초안 등)
    ss.setdefault("max_rev", 2)                        # 최대 재작성 횟수


# ==========================================================================
# 3) 작은 도우미 함수들  ← 여기가 "복잡해서 비워 둔" 부분입니다.
#    지금은 간단/가짜로 동작하고, TODO 부분을 직접 채우면 진짜가 됩니다.
# ==========================================================================
def extract_keywords(text: str) -> list[str]:
    """사용자 문장에서 핵심 키워드만 뽑아냅니다.

    지금은 아주 단순하게 '띄어쓰기로 자르고 2글자 이상'만 남깁니다.
    """
    # TODO: 여기 채우기 —— '뉴스/소식/만들어줘' 같은 불필요한 단어 거르기,
    #       '전기차랑' → '전기차' 처럼 조사 떼기 등을 추가하면 더 똑똑해집니다.
    words = text.split()
    return [w for w in words if len(w) >= 2][:4]   # 최대 4개만


def md_to_html(text: str) -> str:
    """마크다운 글(# 제목, - 목록 등)을 HTML로 바꿔 화면에 예쁘게 보여줍니다.

    지금은 '줄바꿈만' 처리하는 가장 단순한 버전입니다.
    """
    # TODO: 여기 채우기 —— '# 제목' → <h3>, '- 항목' → <li> 처럼
    #       마크다운 기호를 HTML 태그로 바꾸는 규칙을 넣어 보세요.
    return text.replace("\n", "<br>")


def draft_title(draft: str) -> str:
    """초안 글의 맨 위 제목(# 으로 시작하는 줄)을 찾아 돌려줍니다."""
    for line in draft.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "뉴스레터"


# ==========================================================================
# 4) AI 백엔드 연동  ← 여기가 가장 복잡한 부분이라 "가짜"로 비워 뒀습니다.
#    실제로는 app/graph.py 의 그래프를 호출해야 합니다.
#    지금은 화면 흐름을 확인할 수 있도록 가짜 결과를 돌려줍니다.
# ==========================================================================
def run_pipeline(keywords: list[str], max_rev: int) -> dict:
    """키워드를 받아 → 리서치 → 작성 → 검수까지 실행하고 결과를 돌려줍니다."""
    # TODO: 여기 채우기 —— 진짜 AI 그래프 호출.
    #   from app.graph import graph
    #   cfg = {"configurable": {"thread_id": thread_id}}
    #   graph.invoke({"keywords": keywords, ...}, cfg)
    #   그리고 graph.get_state(cfg).values 로 결과를 꺼내 아래 형태로 만들면 됩니다.

    # --- 아래는 화면 테스트용 "가짜 결과" ---
    fake_draft = (
        f"# {', '.join(keywords)} 주간 뉴스레터\n"
        "## 핵심 요약\n"
        "- (예시) 첫 번째 소식입니다.\n"
        "- (예시) 두 번째 소식입니다.\n"
    )
    return {
        "thread_id": uuid.uuid4().hex[:12],
        "status": "awaiting_approval",   # 승인 대기 상태
        "keywords": keywords,
        "draft": fake_draft,
        "review": {"score": 90, "passed": True, "feedback": "예시 검수 코멘트"},
        "revision_count": 0,
        "awaiting_approval": True,
    }


def approve(thread_id: str) -> dict:
    """사람이 '승인'을 누르면 → 발송 단계로 넘어갑니다."""
    # TODO: 여기 채우기 —— graph.invoke(None, cfg) 로 멈춘 지점부터 재개.
    snap = st.session_state.snap
    snap["status"] = "sent"             # 가짜: 그냥 발송 완료로 표시
    snap["awaiting_approval"] = False
    return snap


def reject(thread_id: str, feedback: str) -> dict:
    """사람이 '반려'를 누르면 → 피드백을 반영해 다시 작성합니다."""
    # TODO: 여기 채우기 —— graph.update_state 로 피드백 넣고 다시 invoke.
    snap = st.session_state.snap
    snap["revision_count"] += 1         # 가짜: 재작성 횟수만 +1
    return snap


# ==========================================================================
# 5) 화면(페이지) — 사용자 입력 + 채팅
# ==========================================================================
def page_input():
    st.markdown("## 📝 사용자 입력")

    # (1) 지금까지의 대화를 말풍선으로 그리기
    for m in st.session_state.messages:
        css = "user" if m["role"] == "user" else "bot"
        st.markdown(f'<div class="msg {css}">{m["content"]}</div>',
                    unsafe_allow_html=True)

    # (2) 입력 폼 — 전송 버튼을 누르면 submitted 가 True 가 됩니다.
    with st.form("chat_form", clear_on_submit=True):
        prompt = st.text_input("메시지", placeholder="예: 전기차랑 배터리 소식 정리해줘")
        submitted = st.form_submit_button("전송")

    # (3) 전송됐고 내용이 있으면 → AI 실행
    if submitted and prompt.strip():
        handle_submit(prompt.strip())
        st.rerun()   # 화면을 새로 그려 방금 대화를 반영


def handle_submit(prompt: str):
    """전송 버튼을 눌렀을 때의 처리 흐름 (여기만 보면 동작이 다 보입니다)."""
    # 1. 내가 한 말을 대화에 추가
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 키워드 뽑기
    keywords = extract_keywords(prompt)
    if not keywords:
        st.session_state.messages.append(
            {"role": "assistant", "content": "주제를 조금 더 구체적으로 적어 주세요."})
        return

    # 3. AI 실행 (스피너 = 빙글빙글 도는 표시)
    with st.spinner("뉴스레터를 만드는 중... 🛠️"):
        snap = run_pipeline(keywords, st.session_state.max_rev)

    # 4. 결과 저장 + AI 답변 추가
    st.session_state.thread_id = snap["thread_id"]
    st.session_state.snap = snap
    st.session_state.messages.append({
        "role": "assistant",
        "content": (f"'{', '.join(keywords)}' 뉴스레터를 만들었어요!<br>"
                    f"📰 <b>{draft_title(snap['draft'])}</b><br>"
                    "왼쪽 메뉴 '생성 결과'에서 확인 후 승인/반려해 주세요."),
    })


# ==========================================================================
# 6) 화면(페이지) — 생성 결과 + 승인/반려
# ==========================================================================
def page_result():
    st.markdown("## 📨 생성 결과")
    snap = st.session_state.snap

    if not snap:
        st.info("아직 만든 초안이 없습니다. '사용자 입력'에서 먼저 생성하세요.")
        return

    # (1) 상태 + 초안 본문 보여주기
    st.write(f"상태: **{snap['status']}** · 재작성 {snap['revision_count']}회")
    st.markdown(md_to_html(snap["draft"]), unsafe_allow_html=True)

    # (2) 아직 승인 대기 중이면 → 승인 / 반려 버튼
    if snap.get("awaiting_approval"):
        feedback = st.text_input("반려 시 수정 요청(선택)", placeholder="예: 더 짧게")
        c1, c2 = st.columns(2)

        if c1.button("✅ 승인 → 발송", use_container_width=True):
            st.session_state.snap = approve(st.session_state.thread_id)
            st.rerun()

        if c2.button("↩️ 반려 → 재작성", use_container_width=True):
            st.session_state.snap = reject(st.session_state.thread_id, feedback.strip())
            st.rerun()

    elif snap["status"] == "sent":
        st.success("✅ 발송 완료!")


# ==========================================================================
# 7) 사이드바(왼쪽 메뉴) + 페이지 전환
#    - 메뉴를 추가하려면 PAGES 리스트에 (이름, 함수) 한 줄만 더하면 됩니다.
# ==========================================================================
PAGES = {
    "📝 사용자 입력": page_input,
    "📨 생성 결과": page_result,
}


def render_sidebar() -> str:
    """왼쪽 메뉴를 그리고, 사용자가 고른 페이지 이름을 돌려줍니다."""
    with st.sidebar:
        st.markdown("### 📰 뉴스레터 에이전트")
        st.session_state.max_rev = st.number_input(
            "최대 재작성 횟수", min_value=1, max_value=5,
            value=st.session_state.max_rev,
        )
        choice = st.radio("메뉴", list(PAGES.keys()))
    return choice


# ==========================================================================
# 8) 프로그램 시작점 (맨 위에서부터 순서대로 실행됩니다)
# ==========================================================================
def main():
    setup_page()                 # 1. 페이지 기본 설정
    inject_css()                 # 2. 화면 꾸미기
    init_state()                 # 3. 기억 상자 준비
    choice = render_sidebar()    # 4. 왼쪽 메뉴 그리기
    PAGES[choice]()              # 5. 고른 메뉴의 페이지 함수 실행


main()
