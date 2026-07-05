import os
import json
import re
import operator
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
from openai import OpenAI
import streamlit as st

# 1. State 정의
class FoodState(TypedDict, total=False):
    raw_input: str  # 사용자 입력 (기분, 상황 등)
    mood: Literal["happy", "sad", "stressed", "energetic", "unknown"]
    strategy: Literal["comfort", "celebration", "healthy", "random"]
    recommendation_json: Dict[str, Any]
    final_report: str
    safety_error: str
    trace: Annotated[List[str], operator.add]

# 2. System Prompts
MOOD_SYSTEM_PROMPT = """
너는 사용자의 문장을 보고 기분을 분석하는 분석가다. 
반드시 happy, sad, stressed, energetic, unknown 중 하나만 JSON으로 반환해라.
예: {"mood": "happy"}
"""

RECOM_SYSTEM_PROMPT = """
너는 기분과 추천 전략에 맞춰 음식을 추천하는 미식가다. 
음식 이름, 추천 이유, 어울리는 음료를 JSON으로 반환해라.
예: {"food_name": "김치찌개", "reason": "매콤함으로 스트레스 해소", "pairing": "쿨피스"}
"""

# 3. Nodes
def detect_mood_node(state: FoodState) -> Dict[str, Any]:
    # 실제 구현시에는 LLM 호출 (여기서는 간단히 예시 로직)
    text = state["raw_input"]
    mood = "unknown"
    if "기뻐" in text or "좋아" in text: mood = "happy"
    elif "슬퍼" in text or "우울" in text: mood = "sad"
    elif "짜증" in text or "스트레스" in text: mood = "stressed"
    return {"mood": mood, "trace": [f"Mood Detected: {mood}"]}

def strategy_router_node(state: FoodState) -> Dict[str, Any]:
    mood = state["mood"]
    strategy = "random"
    if mood == "happy": strategy = "celebration"
    elif mood == "sad": strategy = "comfort"
    elif mood == "stressed": strategy = "healthy"
    return {"strategy": strategy, "trace": [f"Strategy Selected: {strategy}"]}

def recommend_food_node(state: FoodState) -> Dict[str, Any]:
    # 추천 로직
    mood = state["mood"]
    strategy = state["strategy"]
    recom = {"food_name": "떡볶이", "reason": f"{mood}한 기분에 {strategy}를 위해 추천합니다.", "pairing": "우유"}
    return {"recommendation_json": recom, "trace": ["Food Recommended"]}

def report_node(state: FoodState) -> Dict[str, Any]:
    recom = state["recommendation_json"]
    report = f"### 오늘의 추천 메뉴: {recom['food_name']}\n**이유**: {recom['reason']}\n**꿀조합**: {recom['pairing']}"
    return {"final_report": report, "trace": ["Report Generated"]}


from langgraph.graph import StateGraph, START, END
import importlib.util

spec = importlib.util.spec_from_file_location("food_core", "parts/01_food_core.py")
food_core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(food_core)

def build_food_graph():
    builder = StateGraph(food_core.FoodState)
    
    builder.add_node("detect_mood", food_core.detect_mood_node)
    builder.add_node("decide_strategy", food_core.strategy_router_node)
    builder.add_node("recommend", food_core.recommend_food_node)
    builder.add_node("report", food_core.report_node)
    
    builder.add_edge(START, "detect_mood")
    builder.add_edge("detect_mood", "decide_strategy")
    builder.add_edge("decide_strategy", "recommend")
    builder.add_edge("recommend", "report")
    builder.add_edge("report", END)
    
    return builder.compile()

print("Food Recommendation Graph Ready")


import streamlit as st
from typing import Dict, Any
import importlib.util

# Dynamic loading utility
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

food_graph_mod = load_module("food_graph", "parts/02_food_graph.py")

def main():
    st.set_page_config(page_title="Mood Food AI", page_icon="🍴")
    st.title("🍴 기분 맞춤 음식 추천 비서")
    
    if "food_messages" not in st.session_state:
        st.session_state.food_messages = []

    user_input = st.text_input("지금 기분이 어떠신가요?", placeholder="예: 너무 우울해서 매운게 당겨, 오늘 면접 합격해서 기분 최고야!")

    if st.button("추천받기") and user_input:
        graph = food_graph_mod.build_food_graph()
        result = graph.invoke({"raw_input": user_input, "trace": []})
        
        st.session_state.food_messages.append({"input": user_input, "report": result["final_report"]})

    for msg in reversed(st.session_state.food_messages):
        st.info(f"💭 입력: {msg['input']}")
        st.markdown(msg['report'])
        st.divider()

if __name__ == "__main__":
    main()
