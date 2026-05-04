import json
import yfinance as yf


def get_stock_price(symbol: str) -> str:
    """Get the current stock price and key metrics for a ticker symbol.
    Returns JSON with: symbol, name, price, change, change_pct, open, volume,
    market_cap, day_high, day_low, week_52_high, week_52_low, pe_ratio, currency.
    Params:
      symbol (str, required) — ticker symbol e.g. 'AAPL', 'TSLA', 'TSM', 'LMT'
    """
    try:
        t = yf.Ticker(symbol.upper())
        info = t.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or price

        if not price:
            hist = t.history(period="2d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price

        change = round(price - prev_close, 4) if price and prev_close else None
        change_pct = round((change / prev_close) * 100, 2) if change and prev_close else None

        return json.dumps({
            "symbol": symbol.upper(),
            "name": info.get("shortName") or info.get("longName", symbol),
            "price": round(price, 2) if price else None,
            "change": change,
            "change_pct": change_pct,
            "open": round(info.get("open") or info.get("regularMarketOpen") or 0, 2) or None,
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "pe_ratio": info.get("trailingPE"),
            "currency": info.get("currency", "USD"),
        }, ensure_ascii=False)
    except Exception as e:
        return f"Error fetching {symbol}: {e}"


def get_multiple_stock_prices(symbols: str) -> str:
    """Get current prices for multiple stocks at once.
    Returns a JSON list of stock objects (same fields as get_stock_price).
    Params:
      symbols (str, required) — comma-separated ticker symbols e.g. 'AAPL,MSFT,TSLA,LMT'
    """
    results = []
    for sym in symbols.split(","):
        sym = sym.strip().upper()
        if not sym:
            continue
        result = get_stock_price(sym)
        try:
            results.append(json.loads(result))
        except Exception:
            results.append({"symbol": sym, "error": result})
    return json.dumps(results, ensure_ascii=False, indent=2)


def get_stock_history(symbol: str, period: str = "1mo") -> str:
    """Get historical price data (OHLCV) for a stock.
    Returns JSON with dates, open, high, low, close, volume arrays.
    Params:
      symbol (str, required) — ticker symbol e.g. 'AAPL'
      period (str, default '1mo') — '1d','5d','1mo','3mo','6mo','1y','2y','5y'
    """
    try:
        t = yf.Ticker(symbol.upper())
        hist = t.history(period=period)
        if hist.empty:
            return f"No history found for {symbol}"
        return json.dumps({
            "symbol": symbol.upper(),
            "period": period,
            "dates":  [d.strftime("%Y-%m-%d") for d in hist.index],
            "open":   [round(float(v), 2) for v in hist["Open"]],
            "high":   [round(float(v), 2) for v in hist["High"]],
            "low":    [round(float(v), 2) for v in hist["Low"]],
            "close":  [round(float(v), 2) for v in hist["Close"]],
            "volume": [int(v) for v in hist["Volume"]],
        }, ensure_ascii=False)
    except Exception as e:
        return f"Error: {e}"
