#!/usr/bin/env python3
"""
Demo so sánh Chatbot baseline vs ReAct Agent.
Chạy: .venv/bin/python demo.py "Giá AAPL hôm nay bao nhiêu?"
"""

import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))

from src.agent.agent import ReActAgent
from src.tools.finance_tools import FINANCE_TOOLS
from src.tools.visual_tools import VISUAL_TOOLS
from test_chatbot import create_llm, run_chatbot

ALL_TOOLS = FINANCE_TOOLS + VISUAL_TOOLS


def run_demo(question: str) -> dict:
    llm = create_llm()
    return {
        "chatbot": run_chatbot(llm, question),
        "agent": ReActAgent(llm, ALL_TOOLS, max_steps=10).run(question),
    }


def print_result(title: str, data: dict):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    print(f"  Latency: {data['latency_ms']}ms | Tools used: {data['tools_used']}")

    for step in data.get("trace", []):
        print(f"\n  [{step['label']}]")
        content = step["content"]
        if len(content) > 400:
            print(f"  {content[:400]}...")
        else:
            print(f"  {content}")

    print(f"\n  >>> ANSWER:\n  {data['answer'][:600]}")
    if len(data["answer"]) > 600:
        print("  ...")


def main():
    question = " ".join(sys.argv[1:]) or (
        "Hãy phân tích cổ phiếu Apple (AAPL): giá hiện tại, ngành nghề và tin tức mới nhất."
    )

    print(f"Câu hỏi: {question}\n")
    try:
        llm = create_llm()
    except RuntimeError as e:
        raise SystemExit(f"❌ {e}")

    print(f"LLM: {llm.model_name} ({type(llm).__name__})")

    chatbot = run_chatbot(llm, question)
    agent = ReActAgent(llm, ALL_TOOLS, max_steps=10).run(question)

    print_result("CHATBOT BASELINE (test_chatbot.py)", chatbot)
    print_result("REACT AGENT (finance + visual tools)", agent)


if __name__ == "__main__":
    main()
