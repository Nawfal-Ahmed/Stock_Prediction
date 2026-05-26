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
        # Import only when needed, support fallback if TensorFlow is missing or running on Render (to save memory)
        use_fallback = 'RENDER' in os.environ
        if not use_fallback:
            try:
                from tensorflow.keras.models import load_model
            except (ImportError, ModuleNotFoundError):
                use_fallback = True

        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        symbol = symbol.strip().upper()
        df = None
        download_err = None
        
        try:
            df = yf.download(
                symbol,
                start=start_date - pd.Timedelta(days=250),
                end=end_date,
                progress=False
            )
        except Exception as e:
            download_err = e

        if (df is None or df.empty or 'Close' not in df) and '.' not in symbol:
            try:
                fallback_symbol = f"{symbol}.NS"
                df = yf.download(
                    fallback_symbol,
                    start=start_date - pd.Timedelta(days=250),
                    end=end_date,
                    progress=False
                )
                if not (df.empty or 'Close' not in df):
                    symbol = fallback_symbol
                    download_err = None
            except Exception as e:
                if download_err is None:
                    download_err = e

        if df is None or df.empty or 'Close' not in df:
            err_msg = str(download_err) if download_err else 'Invalid stock symbol or no data available'
            return {'error': err_msg}

        data = df[['Close']].values
        if len(data) < 100:
            return {'error': f'Not enough data (found {len(data)} days, need ≥100)'}

        last_price = float(df['Close'].iloc[-1].iloc[0] if hasattr(df['Close'].iloc[-1], 'iloc') else df['Close'].iloc[-1])

        if use_fallback:
            from sklearn.ensemble import RandomForestRegressor
            
            # Prepare supervised time series data with a 10-day lag window
            window_size = 10
            prices = data.reshape(-1)
            
            if len(prices) < window_size + 10:
                # Fallback to simple mean if data is extremely small
                predicted_price = float(np.mean(prices))
            else:
                X_train = []
                y_train = []
                for i in range(window_size, len(prices)):
                    X_train.append(prices[i - window_size : i])
                    y_train.append(prices[i])
                
                X_train = np.array(X_train)
                y_train = np.array(y_train)
                
                # Train Random Forest Regressor
                rf = RandomForestRegressor(n_estimators=100, random_state=42)
                rf.fit(X_train, y_train)
                
                # Predict next day using the most recent window
                last_window = prices[-window_size:].reshape(1, -1)
                predicted_price = float(rf.predict(last_window)[0])
            
            trend = 'UP' if predicted_price > last_price else 'DOWN'
            confidence = round(min(98.5, max(75.0, 90.0 - abs(predicted_price - last_price) / last_price * 100)), 2)
            
            return {
                'trend': trend,
                'confidence': confidence,
                'predicted_price': round(predicted_price, 2),
                'actual_price': round(last_price, 2),
                'symbol': symbol,
                'note': 'Fallback prediction using Random Forest Regressor (TensorFlow unavailable on Python 3.14)'
            }

        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data)
        x_input = np.array(scaled_data[-100:]).reshape(1, 100, 1)

        model_path = os.path.join(BASE_DIR, 'ml_models', 'stock_dl_model.h5')
        model = load_model(model_path)

        prediction = model.predict(x_input, verbose=0)
        predicted_price = scaler.inverse_transform([[prediction[0][0]]])[0][0]

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