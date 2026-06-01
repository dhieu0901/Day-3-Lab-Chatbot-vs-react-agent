import os
import sys
import time

from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

CHATBOT_SYSTEM = (
    "Bạn là một trợ lý tài chính thông minh. "
    "Hãy trả lời câu hỏi của người dùng tốt nhất có thể."
)


def create_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

    if provider in ("openai",):
        from src.core.openai_provider import OpenAIProvider
        key = os.getenv("OPENAI_API_KEY", "")
        if not key or key.startswith("your_"):
            raise RuntimeError("Thiếu OPENAI_API_KEY trong .env")
        return OpenAIProvider(model_name=model, api_key=key)

    if provider in ("gemini", "google"):
        from src.core.gemini_provider import GeminiProvider
        key = os.getenv("GEMINI_API_KEY", "")
        if not key or key.startswith("your_"):
            raise RuntimeError("Thiếu GEMINI_API_KEY trong .env")
        return GeminiProvider(model_name=model or "gemini-2.0-flash", api_key=key)

    if provider == "local":
        from src.core.local_provider import LocalProvider
        path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=path)

    raise ValueError(f"Unsupported provider: {provider}")


def run_chatbot(llm, question: str) -> dict:
    """Baseline chatbot — chỉ LLM, không tools (giống lab test_chatbot)."""
    start = time.time()
    full_prompt = f"{CHATBOT_SYSTEM}\n\nUser: {question}\nChatbot:"
    response = llm.generate(full_prompt)

    if isinstance(response, dict):
        answer = response.get("content", str(response))
    else:
        answer = str(response)

    latency_ms = int((time.time() - start) * 1000)
    return {
        "mode": "chatbot",
        "answer": answer,
        "trace": [
            {
                "type": "info",
                "label": "Chatbot (baseline)",
                "content": "Chỉ dùng prompt — không có tools, không dữ liệu live.",
            },
            {"type": "llm", "label": "LLM Response", "content": answer},
        ],
        "tools_used": 0,
        "latency_ms": latency_ms,
    }


def main():
    print("=== Khởi động Baseline Chatbot (Không có Tools) ===")

    llm = create_llm()
    print(f"Loading {os.getenv('DEFAULT_PROVIDER', 'openai')} with model {llm.model_name}...")

    user_query = (
        "Hãy phân tích cổ phiếu Nvidia (NVDA) và Apple (AAPL) cho tôi. Cụ thể: "
        "1. Lấy vài tin tức mới nhất của 2 cổ phiếu. "
        "2. Tính toán các chỉ số kỹ thuật (SMA, RSI) để xem xu hướng hiện tại. "
        "3. Vẽ biểu đồ giá trong 6 tháng qua của 2 cổ phiếu. "
        "Cuối cùng, tổng hợp lại và cho tôi lời khuyên đầu tư. "
        "Trả lời bằng tiếng Việt, giải thích rõ ràng."
    )
    print(f"\nUser Query: {user_query}")
    print("\n--- Chatbot đang trả lời ---")

    result = run_chatbot(llm, user_query)
    print("\n=== FINAL ANSWER (CHATBOT) ===")
    print(result["answer"])


if __name__ == "__main__":
    main()
