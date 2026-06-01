import os
import sys
from dotenv import load_dotenv
from src.agent.agent import ReActAgent
from src.tools.finance_tools import FINANCE_TOOLS

# Fix encoding issue on Windows terminal
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def main():
    print("=== Khởi động ReAct Agent ===")
    
    # 1. Chọn LLM Provider từ cấu hình .env
    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    model = os.getenv("DEFAULT_MODEL", "gpt-4o")
    
    print(f"Loading {provider} provider with model {model}...")
    
    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider
        llm = OpenAIProvider(model_name=model)
    elif provider == "gemini":
        from src.core.gemini_provider import GeminiProvider
        llm = GeminiProvider(model_name=model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # 2. Khởi tạo Agent với các tool chứng khoán và biểu đồ
    from src.tools.visual_tools import VISUAL_TOOLS
    all_tools = FINANCE_TOOLS + VISUAL_TOOLS
    agent = ReActAgent(llm=llm, tools=all_tools, max_steps=10)
    
    # 3. Chạy thử nghiệm
    user_query = "Hãy phân tích cổ phiếu Nvidia (NVDA) cho tôi. Cụ thể: 1. Lấy vài tin tức mới nhất. 2. Tính toán các chỉ số kỹ thuật (SMA, RSI) để xem xu hướng hiện tại. 3. Vẽ biểu đồ giá trong 6 tháng qua. Cuối cùng, tổng hợp lại và cho tôi lời khuyên đầu tư. Trả lời bằng tiếng Việt, giải thích rõ ràng."
    print(f"\nUser Query: {user_query}")
    
    print("\n--- Bắt đầu suy nghĩ ---")
    final_answer = agent.run(user_input=user_query)
    
    print("\n=== FINAL ANSWER ===")
    print(final_answer)

if __name__ == "__main__":
    main()
