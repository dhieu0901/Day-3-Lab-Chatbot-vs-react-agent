import json
import yfinance as yf

def get_company_info(ticker: str) -> str:
    """
    Lấy thông tin tổng quan của một công ty.
    
    Args:
        ticker (str): Mã chứng khoán (VD: "AAPL", "NVDA", "MSFT")
        
    Returns:
        JSON string chứa thông tin công ty như tên, ngành nghề, tóm tắt, CEO, vốn hóa.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Chỉ trích xuất các trường quan trọng để tránh quá tải context của LLM
        filtered_info = {
            "status": "ok",
            "name": info.get("shortName", info.get("longName", ticker)),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "summary": info.get("longBusinessSummary", "N/A"),
            "website": info.get("website", "N/A")
        }
        return json.dumps(filtered_info, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def get_stock_price(ticker: str) -> str:
    """
    Lấy giá cổ phiếu hiện tại và các chỉ số giá cơ bản.
    
    Args:
        ticker (str): Mã chứng khoán (VD: "AAPL")
        
    Returns:
        JSON string chứa giá hiện tại, giá mở cửa, cao nhất, thấp nhất trong ngày.
    """
    try:
        stock = yf.Ticker(ticker)
        # Lấy data của ngày gần nhất
        hist = stock.history(period="1d")
        if hist.empty:
            return json.dumps({"status": "error", "message": f"No price data found for {ticker}"})
        
        latest_data = hist.iloc[-1]
        price_info = {
            "status": "ok",
            "ticker": ticker.upper(),
            "current_price": round(latest_data["Close"], 2),
            "open": round(latest_data["Open"], 2),
            "high": round(latest_data["High"], 2),
            "low": round(latest_data["Low"], 2),
            "volume": int(latest_data["Volume"]),
            "currency": stock.info.get("currency", "USD")
        }
        return json.dumps(price_info, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def get_stock_news(ticker: str) -> str:
    """
    Lấy tin tức mới nhất về một mã cổ phiếu.
    
    Args:
        ticker (str): Mã chứng khoán (VD: "NVDA")
        
    Returns:
        JSON string chứa danh sách các bài báo mới nhất (tiêu đề, link, nguồn, thời gian).
    """
    try:
        stock = yf.Ticker(ticker)
        news_list = stock.news
        
        if not news_list:
            return json.dumps({"status": "no_news", "message": f"No news found for {ticker}"})
        
        results = []
        # Lấy tối đa 5 tin tức
        for news in news_list[:5]:
            content = news.get("content", {})
            provider = content.get("provider", {})
            link = content.get("clickThroughUrl", {}) or content.get("canonicalUrl", {})
            
            results.append({
                "title": content.get("title", "No Title"),
                "publisher": provider.get("displayName", "Unknown"),
                "link": link.get("url", "") if isinstance(link, dict) else "",
                "timestamp": content.get("pubDate", "")
            })
            
        return json.dumps({"status": "ok", "news": results}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ── Tool registry cho Agent ───────────────────────────────────────────────────

FINANCE_TOOLS = [
    {
        "name": "get_company_info",
        "description": "Get general information about a company (sector, industry, summary, market cap) given its ticker symbol (e.g. AAPL).",
        "function": get_company_info,
    },
    {
        "name": "get_stock_price",
        "description": "Get the current stock price and daily trading range for a given ticker symbol.",
        "function": get_stock_price,
    },
    {
        "name": "get_stock_news",
        "description": "Get the latest news headlines and articles for a given stock ticker.",
        "function": get_stock_news,
    }
]

# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_ticker = "AAPL"
    print(f"=== TEST: YFinance Tools for {test_ticker} ===\n")
    
    print("1. get_stock_price()")
    price_res = json.loads(get_stock_price(test_ticker))
    if price_res["status"] == "ok":
        print(f"  Current Price: {price_res['current_price']} {price_res['currency']}")
    else:
        print(f"  Error: {price_res.get('message')}")
        
    print("\n2. get_company_info()")
    info_res = json.loads(get_company_info(test_ticker))
    if info_res["status"] == "ok":
        print(f"  Name: {info_res['name']}")
        print(f"  Sector: {info_res['sector']}")
        summary = info_res['summary']
        print(f"  Summary: {summary[:100]}...")
    else:
        print(f"  Error: {info_res.get('message')}")
        
    print("\n3. get_stock_news()")
    news_res = json.loads(get_stock_news(test_ticker))
    if news_res["status"] == "ok":
        for i, news in enumerate(news_res['news']):
            print(f"  [{i+1}] {news['title']} ({news['publisher']})")
            print(f"      Link: {news['link']}")
    else:
        print(f"  Error/No news: {news_res.get('message')}")
