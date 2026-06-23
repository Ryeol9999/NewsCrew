"""맞춤형 뉴스레터 자동 검수 에이전트 — Streamlit UI.

index.html 화면을 DE_Zoomcamp 스타일(커스텀 CSS 주입 + 메뉴/푸터 숨김)의
Streamlit 페이지로 옮긴 버전입니다. 화면 동작은 JS Mock 대신 실제
LangGraph 백엔드(app/graph.py)에 연결되어 있습니다.

실행:
    cd MVP
    streamlit run streamlit_app.py
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from html import escape as _esc

import streamlit as st

from app.graph import graph

# ==========================================================================
# 페이지 설정 + 테마 (DE_Zoomcamp 템플릿: 커스텀 CSS 주입 / 메뉴·푸터 숨김)
# ==========================================================================
st.set_page_config(
    page_title="맞춤형 뉴스레터 자동 검수 에이전트 — MVP",
    page_icon="📰",
    layout="wide",
)

st.markdown(
    """
<style>
:root{
  /* DE Zoomcamp navy 테마와 조화되는 팔레트 (배경/글자는 config.toml 이 담당) */
  --panel:#1a1a3d; --panel2:#252b54; --logbg:#11152e;
  --line:#3a4170; --text:#f8f8f2; --muted:#9aa6cf;
  --blue:#5681d0; --purple:#b08cff; --cyan:#6ea8ff; --orange:#f5a623;
  --green:#3ecf8e; --red:#ef5b6e;
}
#MainMenu, footer {visibility:hidden;}
.block-container{ padding-top:2.5rem; max-width:1100px; }

/* 헤더 */
.kicker{ color:var(--cyan); letter-spacing:3px; font-size:13px; font-weight:700; }
.nl-h1{ font-size:34px; margin:6px 0 4px; font-weight:800; }
.nl-sub{ color:var(--muted); margin-bottom:22px; }

/* 6단계 파이프라인 */
.steps{ display:grid; grid-template-columns:repeat(6,1fr); gap:6px; margin:6px 0 22px; }
.step{
  background:var(--panel); border:1px solid var(--line); border-radius:9px;
  padding:10px 6px; text-align:center;
  display:flex; align-items:center; justify-content:center; gap:7px;
}
.step .ico{
  width:26px; height:26px; border-radius:50%; flex:0 0 auto;
  display:flex; align-items:center; justify-content:center; font-size:13px;
  background:var(--panel2);
}
.step .name{ font-weight:700; font-size:12px; line-height:1.15; }
.step.active{ border-color:var(--cyan); box-shadow:0 0 0 2px rgba(110,168,255,.25); }
.step.active .ico{ background:var(--cyan); color:#0a1330; }
.step.done .ico{ background:var(--green); color:#04261b; }
.step.fail .ico{ background:var(--red); color:#2b0606; }

/* 카드/리포트 */
.card{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:22px; }
.report h3{ margin:0 0 12px; font-size:20px; }
.report h4{ color:var(--cyan); font-size:15px; margin:18px 0 6px;
  border-left:3px solid var(--cyan); padding-left:8px; }
.report ul{ margin:6px 0; padding-left:22px; }
.report li{ margin:4px 0; }
.report p{ margin:6px 0; }
.report blockquote{ color:var(--muted); border-left:3px solid var(--line);
  padding-left:10px; margin:8px 0; font-size:13px; }

/* 로그 콘솔 */
.log{
  background:var(--logbg); border:1px solid var(--line); border-radius:10px;
  padding:14px; font-family:Consolas,monospace; font-size:13px;
  max-height:220px; overflow:auto; white-space:pre-wrap;
}
.t-research{color:var(--purple)} .t-write{color:var(--blue)}
.t-review{color:var(--cyan)} .t-fail{color:var(--red)}
.t-ok{color:var(--green)} .t-sys{color:var(--muted)}

/* 상태 배지 */
.badge{ display:inline-block; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
.b-wait{ background:rgba(245,158,11,.18); color:var(--orange); border:1px solid var(--orange); }
.b-sent{ background:rgba(16,185,129,.18); color:var(--green); border:1px solid var(--green); }
.kw-chip{ display:inline-block; background:rgba(110,168,255,.18); color:var(--cyan);
  border:1px solid var(--cyan); border-radius:20px; padding:1px 10px; margin:2px 3px 0 0;
  font-size:13px; font-weight:700; }
.meta{ color:var(--muted); font-size:12px; }

/* 채팅창 (index.html .chat 포팅) */
.chat{
  background:var(--logbg); border:1px solid var(--line); border-radius:12px;
  padding:16px; height:380px; overflow-y:auto;
  display:flex; flex-direction:column; gap:10px;
}
.chat .msg{
  max-width:82%; padding:11px 15px; border-radius:14px;
  font-size:15px; line-height:1.5; white-space:pre-wrap; word-break:break-word;
}
.chat .msg.bot{ background:var(--panel); border:1px solid var(--line);
  align-self:flex-start; border-bottom-left-radius:4px; }
.chat .msg.user{ background:var(--blue); color:#fff;
  align-self:flex-end; border-bottom-right-radius:4px; }
.chat .msg b{ font-weight:700; }
.chat .msg .kw-chip{ font-size:13px; }

/* 좌측 메뉴(사이드바) */
section[data-testid="stSidebar"]{ border-right:1px solid var(--line); }
.sb-brand{ font-size:18px; font-weight:800; margin:4px 0 2px; }
.sb-sub{ color:var(--muted); font-size:12px; margin-bottom:6px; }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================================================
# 세션 상태
# ==========================================================================
def _init_state():
    ss = st.session_state
    ss.setdefault("messages", [
        {"role": "assistant",
         "content": "안녕하세요! 어떤 주제의 뉴스레터를 받아보고 싶으세요?\n"
                    "자연어로 편하게 말씀해 주세요. 🙂"},
    ])
    ss.setdefault("thread_id", None)
    ss.setdefault("snap", None)        # 현재 그래프 스냅샷
    ss.setdefault("log", [])           # 실행 로그 (HTML 라인)
    ss.setdefault("history", [])       # 발송 완료 이력
    ss.setdefault("max_rev", 2)


_init_state()

# ==========================================================================
# 자연어 → 키워드 추출 (index.html extractKeywords 포팅)
# ==========================================================================
_STOP = {
    "뉴스레터", "뉴스", "소식", "기사", "정리", "관련", "대해", "대한", "요즘", "최근", "오늘",
    "만들어줘", "만들어", "만들", "해줘", "알려줘", "알려", "보여줘", "정리해줘", "작성해줘",
    "작성", "부탁해", "주제", "내용", "으로", "로", "에", "대", "좀", "것", "거", "수", "및",
    "그리고", "그", "이", "저",
}
_PARTICLE = re.compile(r"(이랑|랑|하고|와|과|이나|나|에서|에게|의|을|를|은|는|이|가|와의|및)$")
_SUFFIX = re.compile(r"(관련|소식|뉴스|기사|동향|이야기|정보)$")


def extract_keywords(text: str) -> list[str]:
    raw = re.sub(r"[.,!?~\"'·]", " ", text).split()
    out, seen = [], set()
    for tok in raw:
        tok = _SUFFIX.sub("", _PARTICLE.sub("", tok)).strip()
        if len(tok) >= 2 and tok not in _STOP and tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out[:4]


# ==========================================================================
# 마크다운 → HTML (index.html mdToHtml 포팅)
# ==========================================================================
def md_to_html(text: str) -> str:
    html, in_list = [], False

    def close_list():
        nonlocal in_list
        if in_list:
            html.append("</ul>")
            in_list = False

    for line in text.split("\n"):
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        if line.startswith("## "):
            close_list(); html.append(f"<h4>{line[3:]}</h4>")
        elif line.startswith("# "):
            close_list(); html.append(f"<h3>{line[2:]}</h3>")
        elif line.startswith("> "):
            close_list(); html.append(f"<blockquote>{line[2:]}</blockquote>")
        elif line.startswith("- "):
            if not in_list:
                html.append("<ul>"); in_list = True
            html.append(f"<li>{line[2:]}</li>")
        elif line.strip() == "":
            close_list(); html.append("<br>")
        else:
            close_list(); html.append(f"<p>{line}</p>")
    close_list()
    return "".join(html)


def draft_title(draft: str) -> str:
    for line in draft.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "뉴스레터"


def build_doc(title: str, body: str, keywords: list[str], date: str) -> bytes:
    """index.html downloadDoc 과 동일한 Word(.doc) HTML 생성."""
    doc = (
        "<html xmlns:o='urn:schemas-microsoft-com:office:office' "
        "xmlns:w='urn:schemas-microsoft-com:office:word' "
        "xmlns='http://www.w3.org/TR/REC-html40'>"
        f"<head><meta charset='utf-8'><title>{title}</title>"
        "<style>body{font-family:'맑은 고딕',sans-serif;font-size:11pt;line-height:1.6;color:#222}"
        "h1{font-size:20pt}h4{font-size:13pt;color:#1a5fb4;margin:14pt 0 4pt}"
        "blockquote{color:#666;border-left:3px solid #ccc;padding-left:8pt;margin:6pt 0}"
        "ul{margin:4pt 0}li{margin:2pt 0}</style></head><body>"
        f"<h1>{title}</h1>"
        f"<p style='color:#888'>키워드: {', '.join(keywords)} · 생성일: {date}</p><hr>"
        + md_to_html(body) +
        "</body></html>"
    )
    return ("﻿" + doc).encode("utf-8")


# ==========================================================================
# 그래프 백엔드 연동 (app/graph.py)
# ==========================================================================
def _cfg(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _snapshot(thread_id: str) -> dict:
    state = graph.get_state(_cfg(thread_id))
    v = state.values
    return {
        "thread_id": thread_id,
        "status": v.get("status"),
        "keywords": v.get("keywords", []),
        "research": v.get("research", ""),
        "draft": v.get("draft", ""),
        "review": v.get("review", {}),
        "revision_count": v.get("revision_count", 0),
        "final": v.get("final", ""),
        "next": list(state.next),
        # send 직전 interrupt 로 멈춰 있으면 승인 대기
        "awaiting_approval": "send" in state.next,
    }


def run_pipeline(keywords: list[str], max_rev: int) -> dict:
    """리서치→작성→검수→(복귀 루프)→승인 대기 지점까지 실행."""
    thread_id = uuid.uuid4().hex[:12]
    graph.invoke(
        {"keywords": keywords, "revision_count": 0,
         "max_revisions": max_rev, "status": "researching"},
        _cfg(thread_id),
    )
    return _snapshot(thread_id)


def approve(thread_id: str) -> dict:
    graph.invoke(None, _cfg(thread_id))  # 멈춘 지점부터 재개 → send
    return _snapshot(thread_id)


def reject(thread_id: str, feedback: str) -> dict:
    cfg = _cfg(thread_id)
    graph.update_state(
        cfg,
        {"human_feedback": feedback, "status": "writing"},
        as_node="research",  # research→write 엣지로 작성 단계 재진입
    )
    graph.invoke(None, cfg)
    return _snapshot(thread_id)


def build_log(snap: dict, *, sent: bool = False) -> list[str]:
    """스냅샷으로부터 실행 로그 라인을 재구성."""
    kw = ", ".join(snap["keywords"])
    review = snap.get("review", {})
    revisions = snap.get("revision_count", 0)
    lines = [
        f'<span class="t-sys">▶ 사용자 입력: {kw}</span>',
        '<span class="t-research">[리서치] 자료 수집·정리 완료</span>',
        f'<span class="t-write">[작성] 초안 작성 (총 {revisions}회 작성/재작성)</span>',
    ]
    if review.get("passed"):
        lines.append(f'<span class="t-ok">[검수] 통과 ✓ (점수 {review.get("score")})</span>')
    else:
        lines.append(
            f'<span class="t-fail">[검수] 품질 미달 ✗ (점수 {review.get("score")}) '
            f'→ 최대 재작성 초과, 사람 판단 대기</span>')
    if sent:
        lines.append('<span class="t-ok">[발송] 사람 승인 완료 → 발송 및 이력 저장 ✓</span>')
    else:
        lines.append('<span class="t-sys">[시스템] 그래프 일시 중단 — 사람 승인 대기 '
                     '(interrupt_before=["send"])</span>')
    return lines


# ==========================================================================
# 공통 헤더 / 6단계 파이프라인
# ==========================================================================
HEADER_HTML = """
<div class="kicker">SERVICE SCENARIO · MVP</div>
<div class="nl-h1">맞춤형 뉴스레터 자동 검수 에이전트</div>
<!-- 부제(파이프라인 설명)는 주석처리
<div class="nl-sub">관심 키워드 입력 → 리서치 → 작성 → 검수(품질 미달 시 작성 복귀)
→ 사람 승인 → 발송</div>
-->
"""


def page_title(icon: str, name: str):
    """add_page_title() 대용 — 페이지 상단 타이틀."""
    st.markdown(f'<div class="nl-h1">{icon} {name}</div>', unsafe_allow_html=True)


def render_steps():
    # 6단계 파이프라인 표시는 주석처리 — 다시 보이게 하려면 아래 return 을 제거
    return
    snap = st.session_state.snap
    status = snap["status"] if snap else None
    sent = status == "sent"
    awaiting = bool(snap and snap.get("awaiting_approval"))

    # 단계별 클래스 결정
    cls = ["", "", "", "", "", ""]
    if snap:
        cls[0] = cls[1] = cls[2] = "done"
        review = snap.get("review", {})
        cls[3] = "done" if review.get("passed") else ("fail" if review else "done")
        if sent:
            cls[3] = "done"; cls[4] = "done"; cls[5] = "done"
        elif awaiting:
            cls[4] = "active"

    # steps = [
    #     ("🏷️", "사용자 입력"), ("🔍", "리서치"), ("✏️", "작성"),
    #     ("📋", "검수"), ("🧑‍⚖️", "승인 대기"), ("📤", "발송·저장"),
    # ]
    html = ['<div class="steps">']
    for (ico, name), c in zip(steps, cls):
        html.append(
            f'<div class="step {c}"><div class="ico">{ico}</div>'
            f'<div class="name">{name}</div></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


# ==========================================================================
# 페이지 정의 (좌측 메뉴 = st.navigation 멀티페이지)
# ==========================================================================
def page_home():
    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    render_steps()
    st.markdown(
        "관심 키워드를 입력하면 **리서치 → 작성 → 검수**를 거쳐 뉴스레터 초안을 만들고, "
        "**검수 품질 미달 시 작성 단계로 자동 복귀**하는 순환 루프와 "
        "**사람 승인(Human-in-the-loop)** 후 발송하는 흐름을 시연합니다."
    )
    snap = st.session_state.snap
    status_kr = {None: "대기 중", "awaiting_approval": "승인 대기",
                 "sent": "발송 완료"}.get(snap["status"] if snap else None,
                                       snap["status"] if snap else "대기 중")
    c1, c2, c3 = st.columns(3)
    c1.metric("생성 기록", f"{len(st.session_state.history)} 건")
    c2.metric("현재 상태", status_kr)
    c3.metric("재작성 횟수", f'{snap["revision_count"]} 회' if snap else "-")
    st.info("👈 왼쪽 메뉴에서 **📝 사용자 입력**으로 이동해 시작하세요.")


def page_input():
    # 상단 대타이틀
    st.markdown(
        '<div class="kicker">SERVICE SCENARIO · MVP</div>'
        '<div class="nl-h1">📰 맞춤형 뉴스레터 자동 검수 에이전트</div>',
        unsafe_allow_html=True,
    )

    # 채팅창(말풍선) — index.html 형식: 대화는 박스 안, 입력창은 하단 고정
    bubbles = []
    for m in st.session_state.messages:
        role_cls = "bot" if m["role"] == "assistant" else "user"
        # 어시스턴트 메시지는 HTML(칩/굵게) 그대로, 사용자 메시지는 escape
        content = m["content"] if m["role"] == "assistant" else _esc(m["content"])
        bubbles.append(f'<div class="msg {role_cls}">{content}</div>')
    st.markdown(f'<div class="chat">{"".join(bubbles)}</div>', unsafe_allow_html=True)

    # 입력창 — 채팅창 바로 아래 (st.chat_input 은 화면 맨 아래 고정되므로 폼으로 대체)
    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([6, 1])
        prompt = cols[0].text_input(
            "메시지", label_visibility="collapsed",
            placeholder="예: 요즘 전기차랑 배터리 소식 정리해줘",
        )
        submitted = cols[1].form_submit_button("전송", use_container_width=True)

    # 실행 로그는 접이식으로 (채팅 흐름을 방해하지 않게)
    if st.session_state.log:
        with st.expander("🖥 실행 로그", expanded=False):
            st.markdown(
                f'<div class="log">{"<br>".join(st.session_state.log)}</div>',
                unsafe_allow_html=True,
            )

    if submitted and prompt.strip():
        prompt = prompt.strip()
        st.session_state.messages.append({"role": "user", "content": prompt})
        keywords = extract_keywords(prompt)

        if not keywords:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "관심 있는 주제를 조금 더 구체적으로 말씀해 주세요. "
                           '예: "AI랑 반도체 소식 만들어줘"',
            })
        else:
            chips = "".join(f'<span class="kw-chip">{k}</span>' for k in keywords)
            with st.spinner("뉴스레터를 생성하는 중입니다... 🛠️"):
                snap = run_pipeline(keywords, int(st.session_state.max_rev))
            st.session_state.thread_id = snap["thread_id"]
            st.session_state.snap = snap
            st.session_state.log = build_log(snap)

            review = snap.get("review", {})
            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    f"알겠습니다! 다음 키워드로 뉴스레터를 만들었어요:<br>{chips}<br><br>"
                    f"📰 <b>{draft_title(snap['draft'])}</b><br>"
                    f"검수 점수 <b>{review.get('score', '-')}/100</b> · "
                    f"재작성 {snap['revision_count']}회<br>"
                    "왼쪽 메뉴의 **📨 생성 결과**에서 보고서를 확인하고 승인/반려해 주세요."
                ),
            })
        st.rerun()

# --------------------------------------------------------------------------
# 페이지: 생성 결과 (상세 보고서 + 승인/반려)
# --------------------------------------------------------------------------
def page_result():
    page_title("📨", "생성 결과")
    snap = st.session_state.snap
    if not snap:
        st.markdown(
            '<div class="meta">아직 생성된 초안이 없습니다. '
            '「📝 사용자 입력」 탭에서 생성을 시작하세요.</div>',
            unsafe_allow_html=True,
        )
    else:
        sent = snap["status"] == "sent"
        awaiting = snap.get("awaiting_approval") and not sent
        badge = ('<span class="badge b-sent">✅ 발송 완료</span>' if sent else
                 '<span class="badge b-wait">⏸ 승인 대기 중</span>')
        st.markdown(
            f'{badge} &nbsp; <span class="meta">키워드: '
            f'{", ".join(snap["keywords"])} · 재작성 {snap["revision_count"]}회</span>',
            unsafe_allow_html=True,
        )

        title = draft_title(snap["draft"])
        st.markdown(
            f'<div class="card report">{md_to_html(snap["draft"])}</div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            "⬇ DOC 다운로드",
            data=build_doc(title, snap["draft"], snap["keywords"],
                           datetime.now().strftime("%Y-%m-%d %H:%M")),
            file_name=f"뉴스레터_{'_'.join(snap['keywords'])}.doc",
            mime="application/msword",
        )

        review = snap.get("review", {})
        if review.get("feedback"):
            st.markdown(
                f'<div class="meta">🧾 검수 코멘트: {review["feedback"]} '
                f'(점수 {review.get("score")})</div>',
                unsafe_allow_html=True,
            )

        if awaiting:
            st.divider()
            fb = st.text_input(
                "반려 시 수정 요청 (선택)",
                placeholder="예: 더 짧고 캐주얼하게, 통계 수치 추가",
            )
            c1, c2 = st.columns(2)
            if c1.button("✅ 승인 → 발송", use_container_width=True, type="primary"):
                with st.spinner("발송 중..."):
                    snap = approve(st.session_state.thread_id)
                st.session_state.snap = snap
                st.session_state.log = build_log(snap, sent=True)
                # 이력 저장
                st.session_state.history.insert(0, {
                    "id": uuid.uuid4().hex,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "keywords": snap["keywords"],
                    "revision": snap["revision_count"],
                    "score": snap.get("review", {}).get("score"),
                    "title": draft_title(snap["draft"]),
                    "draft": snap["draft"],
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f'✅ "{", ".join(snap["keywords"])}" 뉴스레터를 발송했어요! '
                               "다른 주제도 말씀해 주세요.",
                })
                st.rerun()
            if c2.button("↩️ 반려 → 재작성", use_container_width=True):
                with st.spinner("피드백을 반영해 다시 작성 중..."):
                    snap = reject(st.session_state.thread_id, fb.strip())
                st.session_state.snap = snap
                st.session_state.log = build_log(snap)
                st.rerun()
        elif sent:
            st.success("발송이 완료되어 「📚 생성 기록」에 저장되었습니다.")

# --------------------------------------------------------------------------
# 페이지: 생성 기록
# --------------------------------------------------------------------------
def page_history():
    page_title("📚", "생성 기록")
    hist = st.session_state.history
    top = st.columns([4, 1])
    top[0].markdown("#### 발송된 뉴스레터")
    if top[1].button("🗑 전체 삭제", use_container_width=True) and hist:
        st.session_state.history = []
        st.rerun()

    if not hist:
        st.markdown('<div class="meta">아직 발송된 뉴스레터가 없습니다.</div>',
                    unsafe_allow_html=True)
    else:
        for r in hist:
            label = (f'{", ".join(r["keywords"])}  ·  점수 {r["score"] or "-"} '
                     f'· 재작성 {r["revision"]}회  ·  {r["date"]}')
            with st.expander(f"📨 {label}"):
                st.markdown(
                    f'<div class="card report">{md_to_html(r["draft"])}</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "⬇ DOC 다운로드",
                    data=build_doc(r["title"], r["draft"], r["keywords"], r["date"]),
                    file_name=f"뉴스레터_{'_'.join(r['keywords'])}.doc",
                    mime="application/msword",
                    key=f"dl_{r['id']}",
                )


# ==========================================================================
# 좌측 메뉴 (DE Zoomcamp 형태)
#  - streamlit >= 1.36 : 네이티브 멀티페이지 st.navigation 사용
#  - 그 이하(예: 1.28) : st.sidebar.radio 로 동일한 좌측 메뉴 제공
# ==========================================================================
# (key, title, icon, 함수)
_MENU = [
    ("home", "홈", "🏠", page_home),
    ("input", "사용자 입력", "📝", page_input),
    ("result", "생성 결과", "📨", page_result),
    ("history", "생성 기록", "📚", page_history),
]

with st.sidebar:
    st.markdown('<div class="sb-brand">📰 뉴스레터 에이전트</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-sub">AI 자동 생성 · 검수 · 발송</div>', unsafe_allow_html=True)
    st.session_state.max_rev = st.number_input(
        "최대 재작성 횟수", min_value=1, max_value=5,
        value=st.session_state.max_rev, step=1,
        help="검수에서 품질 미달 시 작성 단계로 복귀하는 최대 횟수",
    )

if hasattr(st, "navigation") and hasattr(st, "Page"):
    st.navigation([
        st.Page(fn, title=title, icon=icon, default=(i == 0))
        for i, (key, title, icon, fn) in enumerate(_MENU)
    ]).run()
else:
    # 구버전 streamlit 호환: 사이드바 라디오 메뉴
    labels = {key: f"{icon} {title}" for key, title, icon, fn in _MENU}
    funcs = {key: fn for key, title, icon, fn in _MENU}
    with st.sidebar:
        st.markdown("---")
        choice = st.radio(
            "메뉴", list(labels), format_func=lambda k: labels[k],
            key="nav", label_visibility="collapsed",
        )
    funcs[choice]()
