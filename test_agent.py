import os
import sys
from dotenv import load_dotenv
from src.agent.agent import ReActAgent
from src.tools.finance_tools import FINANCE_TOOLS
from test_chatbot import create_llm

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


def main():
    print("=== Khởi động ReAct Agent ===")

    llm = create_llm()
    print(f"Loading {os.getenv('DEFAULT_PROVIDER', 'openai')} with model {llm.model_name}...")

    from src.tools.visual_tools import VISUAL_TOOLS
    all_tools = FINANCE_TOOLS + VISUAL_TOOLS
    agent = ReActAgent(llm=llm, tools=all_tools, max_steps=10)

    user_query = (
        "Hãy phân tích cổ phiếu Nvidia (NVDA) và Apple (AAPL) cho tôi. Cụ thể: "
        "1. Lấy vài tin tức mới nhất của 2 cổ phiếu. "
        "2. Tính toán các chỉ số kỹ thuật (SMA, RSI) để xem xu hướng hiện tại. "
        "3. Vẽ biểu đồ giá trong 6 tháng qua của 2 cổ phiếu. "
        "Cuối cùng, tổng hợp lại và cho tôi lời khuyên đầu tư. "
        "Trả lời bằng tiếng Việt, giải thích rõ ràng."
    )
    print(f"\nUser Query: {user_query}")
    print("\n--- Bắt đầu suy nghĩ ---")

    final_answer = agent.run(user_input=user_query)

    print("\n=== FINAL ANSWER ===")
    if isinstance(final_answer, dict):
        print(final_answer.get("answer", final_answer))
    else:
        print(final_answer)


if __name__ == "__main__":
    main()
