import os
import sys
from dotenv import load_dotenv

# Fix encoding issue on Windows terminal
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def main():
    print("=== Khởi động Baseline Chatbot (Không có Tools) ===")
    
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
    
    # 2. Tạo query phức tạp
    user_query = "Bạn hãy kiểm tra giá cổ phiếu của Apple (AAPL) và NVIDIA (NVDA) hiện tại là bao nhiêu, và tìm xem có tin tức gì mới về Apple và Nvidia không. Dựa vào đó hãy cho tôi lời khuyên về việc nên mua cổ phiếu nào, tại sao? Trả lời bằng tiếng Việt, giải thích rõ ràng"
    print(f"\nUser Query: {user_query}")
    
    # 3. Chạy Chatbot thông thường (Chỉ dùng Prompt, KHÔNG có tools)
    print("\n--- Chatbot đang trả lời ---")
    system_prompt = "Bạn là một trợ lý tài chính thông minh. Hãy trả lời câu hỏi của người dùng tốt nhất có thể."
    
    # Xây dựng prompt đơn giản
    full_prompt = f"{system_prompt}\n\nUser: {user_query}\nChatbot:"
    
    # Gọi LLM sinh text
    response = llm.generate(full_prompt)
    
    print("\n=== FINAL ANSWER (CHATBOT) ===")
    if isinstance(response, dict):
        print(response.get("content", str(response)))
    else:
        print(response)
    
    print("\n--- NHẬN XÉT (PHASE 2) ---")
    print("Quan sát kết quả: Chatbot không có Tool thường sẽ:")
    print("1. Báo lỗi không thể truy cập internet/dữ liệu realtime.")
    print("2. Hoặc bịa đặt (hallucinate) một mức giá cũ từ dữ liệu huấn luyện.")
    print("Điều này làm nổi bật sức mạnh của ReAct Agent trong Phase 3!")

if __name__ == "__main__":
    main()
