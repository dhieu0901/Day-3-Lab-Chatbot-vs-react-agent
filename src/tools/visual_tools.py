import json
import os
import yfinance as yf
import matplotlib.pyplot as plt

def plot_stock_chart(ticker: str) -> str:
    """
    Vẽ biểu đồ giá cổ phiếu trong 6 tháng gần nhất cùng với đường SMA 20 và SMA 50.
    
    Args:
        ticker (str): Mã chứng khoán (VD: "AAPL")
        
    Returns:
        JSON string chứa đường dẫn đến file ảnh biểu đồ.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        if hist.empty:
            return json.dumps({"status": "error", "message": f"No data found for {ticker}"})
            
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        
        # Tạo thư mục charts nếu chưa có
        os.makedirs("charts", exist_ok=True)
        file_path = f"charts/{ticker.upper()}_chart.png"
        
        # Vẽ biểu đồ
        plt.figure(figsize=(10, 5))
        plt.plot(hist.index, hist['Close'], label='Close Price', color='blue')
        plt.plot(hist.index, hist['SMA_20'], label='SMA 20', color='orange', linestyle='--')
        plt.plot(hist.index, hist['SMA_50'], label='SMA 50', color='red', linestyle='-.')
        
        plt.title(f"{ticker.upper()} Stock Price - Last 6 Months")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)
        
        plt.savefig(file_path)
        plt.close()
        
        return json.dumps({
            "status": "ok",
            "message": f"Chart successfully plotted and saved.",
            "file_path": os.path.abspath(file_path)
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ── Tool registry cho Agent ───────────────────────────────────────────────────
VISUAL_TOOLS = [
    {
        "name": "plot_stock_chart",
        "description": "Plot a professional stock price chart for the last 6 months including SMA lines and save it as an image.",
        "function": plot_stock_chart,
    }
]
