# -*- coding: utf-8 -*-

import operator
from typing import Annotated, Any, Dict, List, Literal, TypedDict

import streamlit as st
from langgraph.graph import StateGraph, START, END


# =========================
# 1. State 정의
# =========================

class FoodState(TypedDict, total=False):
    raw_input: str
    mood: Literal["happy", "sad", "stressed", "energetic", "unknown"]
    strategy: Literal["comfort", "celebration", "healthy", "random"]
    recommendation_json: Dict[str, Any]
    final_report: str
    safety_error: str
    trace: Annotated[List[str], operator.add]


# =========================
# 2. Nodes 정의
# =========================

def detect_mood_node(state: FoodState) -> Dict[str, Any]:
    text = state["raw_input"]

    mood = "unknown"

    if "기뻐" in text or "좋아" in text or "최고" in text or "합격" in text:
        mood = "happy"
    elif "슬퍼" in text or "우울" in text:
        mood = "sad"
    elif "짜증" in text or "스트레스" in text:
        mood = "stressed"
    elif "활기" in text or "에너지" in text:
        mood = "energetic"

    return {
        "mood": mood,
        "trace": [f"Mood Detected: {mood}"],
    }


def strategy_router_node(state: FoodState) -> Dict[str, Any]:
    mood = state["mood"]

    strategy = "random"

    if mood == "happy":
        strategy = "celebration"
    elif mood == "sad":
        strategy = "comfort"
    elif mood == "stressed":
        strategy = "healthy"
    elif mood == "energetic":
        strategy = "healthy"

    return {
        "strategy": strategy,
        "trace": [f"Strategy Selected: {strategy}"],
    }


def recommend_food_node(state: FoodState) -> Dict[str, Any]:
    mood = state["mood"]
    strategy = state["strategy"]

    if strategy == "celebration":
        recom = {
            "food_name": "삼겹살",
            "reason": "기분 좋은 날에는 든든하고 분위기 좋은 음식이 잘 어울립니다.",
            "pairing": "탄산음료",
        }
    elif strategy == "comfort":
        recom = {
            "food_name": "김치찌개",
            "reason": "우울하거나 슬픈 날에는 따뜻하고 익숙한 음식이 위로가 됩니다.",
            "pairing": "계란말이",
        }
    elif strategy == "healthy":
        recom = {
            "food_name": "샐러드 보울",
            "reason": "스트레스를 받거나 에너지가 필요할 때는 부담 없는 건강식이 좋습니다.",
            "pairing": "아이스 아메리카노",
        }
    else:
        recom = {
            "food_name": "떡볶이",
            "reason": "특별한 기분이 감지되지 않아 누구나 좋아할 만한 메뉴를 추천합니다.",
            "pairing": "우유",
        }

    return {
        "recommendation_json": recom,
        "trace": ["Food Recommended"],
    }


def report_node(state: FoodState) -> Dict[str, Any]:
    recom = state["recommendation_json"]

    report = f"""
### 오늘의 추천 메뉴: {recom["food_name"]}

**이유**: {recom["reason"]}

**꿀조합**: {recom["pairing"]}
"""

    return {
        "final_report": report,
        "trace": ["Report Generated"],
    }


# =========================
# 3. Graph 정의
# =========================

@st.cache_resource
def build_food_graph():
    builder = StateGraph(FoodState)

    builder.add_node("detect_mood", detect_mood_node)
    builder.add_node("decide_strategy", strategy_router_node)
    builder.add_node("recommend", recommend_food_node)
    builder.add_node("report", report_node)

    builder.add_edge(START, "detect_mood")
    builder.add_edge("detect_mood", "decide_strategy")
    builder.add_edge("decide_strategy", "recommend")
    builder.add_edge("recommend", "report")
    builder.add_edge("report", END)

    return builder.compile()


# =========================
# 4. Streamlit App
# =========================

def main():
    st.set_page_config(
        page_title="Mood Food AI",
        page_icon="🍴",
    )

    st.title("🍴 기분 맞춤 음식 추천 비서")
    st.write("지금 기분을 입력하면 LangGraph가 기분을 분석하고 음식 메뉴를 추천해줍니다.")

    if "food_messages" not in st.session_state:
        st.session_state.food_messages = []

    user_input = st.text_input(
        "지금 기분이 어떠신가요?",
        placeholder="예: 너무 우울해서 매운 게 당겨, 오늘 면접 합격해서 기분 최고야!",
    )

    if st.button("추천받기") and user_input:
        graph = build_food_graph()

        try:
            result = graph.invoke(
                {
                    "raw_input": user_input,
                    "trace": [],
                }
            )

            st.session_state.food_messages.append(
                {
                    "input": user_input,
                    "report": result["final_report"],
                    "trace": result.get("trace", []),
                }
            )

        except Exception as e:
            st.error("추천 생성 중 오류가 발생했습니다.")
            st.exception(e)

    for msg in reversed(st.session_state.food_messages):
        st.info(f"💭 입력: {msg['input']}")
        st.markdown(msg["report"])

        with st.expander("실행 Trace 보기"):
            for t in msg["trace"]:
                st.write(f"- {t}")

        st.divider()


if __name__ == "__main__":
    main()
