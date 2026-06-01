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
    
    # 2. Khởi tạo Agent với các tool chứng khoán
    agent = ReActAgent(llm=llm, tools=FINANCE_TOOLS, max_steps=5)
    
    # 3. Chạy thử nghiệm
    user_query = "Bạn hãy kiểm tra giá cổ phiếu của Apple (AAPL) và NVIDIA (NVDA) hiện tại là bao nhiêu, và tìm xem có tin tức gì mới về Apple và Nvidia không. Dựa vào đó hãy cho tôi lời khuyên về việc nên mua cổ phiếu nào, tại sao?"
    print(f"\nUser Query: {user_query}")
    
    print("\n--- Bắt đầu suy nghĩ ---")
    final_answer = agent.run(user_input=user_query)
    
    print("\n=== FINAL ANSWER ===")
    print(final_answer)

if __name__ == "__main__":
    main()
