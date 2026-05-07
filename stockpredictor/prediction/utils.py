import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
import datetime as dt
import os
from datetime import timedelta, datetime, timezone
import math
from .models import StockInfo
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_stock_data(symbol, start_date, end_date):
    df = yf.download(symbol, start=start_date, end=end_date)
    df = df.reset_index()
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    return df


def prepare_data(df):
    data = df['Close']
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(np.array(data).reshape(-1, 1))
    x_input = []
    for i in range(100, len(scaled_data)):
        x_input.append(scaled_data[i - 100:i])
    x_input = np.array(x_input)
    return x_input, scaler


def predict_trend(symbol, start_date, end_date):
    # Import only when needed
    from tensorflow.keras.models import load_model

    df = load_stock_data(symbol, start_date, end_date)
    if len(df) < 200:
        return {'error': 'Not enough data to predict'}

    model_path = os.path.join(BASE_DIR, 'ml_models', 'stock_dl_model.h5')
    model = load_model(model_path)

    recent_data = df.tail(200).copy()
    x_input, scaler = prepare_data(recent_data)

    prediction = model.predict(x_input)
    scale_factor = 1 / scaler.scale_[0]
    prediction = prediction * scale_factor
    predicted_price = prediction[-1][0]
    last_price = df['Close'].iloc[-1]

    trend = "Up" if predicted_price > last_price else "Down"
    confidence = round(abs(predicted_price - last_price) / last_price * 100, 2)

    return {
        'trend': trend,
        'confidence_score': confidence,
        'predicted_price': round(predicted_price, 2),
        'actual_price': round(last_price, 2),
        'symbol': symbol
    }


def predict_stock_trend(symbol, start_date, end_date):
    try:
        # Import only when needed
        from tensorflow.keras.models import load_model

        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        df = yf.download(
            symbol,
            start=start_date - pd.Timedelta(days=250),
            end=end_date,
            progress=False
        )

        if df.empty or 'Close' not in df:
            return {'error': 'Invalid stock symbol or no data available'}

        data = df[['Close']].values
        if len(data) < 100:
            return {'error': f'Not enough data (found {len(data)} days, need ≥100)'}

        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data)
        x_input = np.array(scaled_data[-100:]).reshape(1, 100, 1)

        model_path = os.path.join(BASE_DIR, 'ml_models', 'stock_dl_model.h5')
        model = load_model(model_path)

        prediction = model.predict(x_input, verbose=0)
        predicted_price = scaler.inverse_transform([[prediction[0][0]]])[0][0]

        last_price = float(df['Close'].iloc[-1])
        trend = 'UP' if predicted_price > last_price else 'DOWN'
        confidence = round(abs(predicted_price - last_price) / last_price * 100, 2)

        return {
            'trend': trend,
            'confidence': confidence,
            'predicted_price': round(predicted_price, 2),
            'actual_price': round(last_price, 2),
            'symbol': symbol
        }

    except Exception as e:
        return {'error': str(e)}


def _full_ticker(symbol: str, exchange: str | None):
    s = symbol.strip().upper()
    ex = exchange.strip().upper() if exchange else "NS"
    suffix = ".NS" if ex in ("NS", "NSE") else (".BO" if ex in ("BSE", "BO") else "")
    return s + suffix


def fetch_quote(symbol: str, exchange: str | None = "NS"):
    tkr = yf.Ticker(_full_ticker(symbol, exchange))
    info = tkr.history(period="2d", interval="1d")
    if info.empty:
        return None
    price = float(info["Close"].iloc[-1])
    prev_close = float(info["Close"].iloc[-2]) if len(info) > 1 else price
    change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0
    name = tkr.info.get("shortName") or tkr.info.get("longName") or symbol
    return {
        "price": round(price, 2),
        "prev_close": round(prev_close, 2),
        "change_pct": round(change_pct, 2),
        "name": name,
        "ts": datetime.now(timezone.utc),
    }


def fetch_sparkline(symbol: str, exchange: str | None = "NS", days: int = 30):
    tkr = yf.Ticker(_full_ticker(symbol, exchange))
    df = tkr.history(period=f"{days}d", interval="1d")
    if df.empty:
        return []
    return [(idx.strftime("%Y-%m-%d"), float(v)) for idx, v in df["Close"].items()]


def fetch_stock_data(symbol="POWERGRID.NS"):
    stock = yf.Ticker(symbol)
    info = stock.info
    stock_info, created = StockInfo.objects.update_or_create(
        symbol=symbol,
        defaults={
            "full_name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap"),
            "previous_close": info.get("previousClose"),
            "current_price": info.get("currentPrice"),
            "dividend_yield": info.get("dividendYield"),
            "pe_ratio": info.get("trailingPE"),
        }
    )
    return stock_info


def run_prediction(symbol, start_date, end_date):
    # Import only when needed
    from .gold_lstm import predict_gold_lstm

    gold_symbols = ["GOLDBEES.NS", "TATAGOLD.NS", "MCXGOLD", "GOLD"]
    if any(g in symbol for g in gold_symbols):
        return predict_gold_lstm(symbol, start_date, end_date)
    else:
        return predict_stock_trend(symbol, start_date, end_date)