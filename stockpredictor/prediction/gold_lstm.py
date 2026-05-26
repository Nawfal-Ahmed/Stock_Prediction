import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

def load_gold_data(symbol, start_date, end_date):
    df = yf.download(symbol, start=start_date, end=end_date)

    if df.empty:
        raise ValueError("No data fetched for GOLD")

    return df[['Close']]

def prepare_data(data, seq_len=60):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data)

    X, y = [], []
    for i in range(seq_len, len(scaled)):
        X.append(scaled[i-seq_len:i])
        y.append(scaled[i])

    return np.array(X), np.array(y), scaler

def build_lstm(input_shape):
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(64),
        Dropout(0.2),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mse')
    return model

def predict_gold_lstm(symbol, start_date, end_date):
    import os
    use_fallback = 'RENDER' in os.environ
    if not use_fallback:
        try:
            from tensorflow.keras.models import Sequential
        except (ImportError, ModuleNotFoundError):
            use_fallback = True

    df = load_gold_data(symbol, start_date, end_date)
    
    if use_fallback:
        from sklearn.linear_model import LinearRegression
        data = df.values
        if len(data) < 60:
            raise ValueError(f"Not enough data (found {len(data)} days, need >=60)")
            
        X, y, scaler = prepare_data(data)
        split = int(0.8 * len(X))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        # Reshape for Linear Regression
        # X is (N, 60, 1), we flatten it to (N, 60) for Linear Regression
        X_train_flat = X_train.reshape(X_train.shape[0], -1)
        X_test_flat = X_test.reshape(X_test.shape[0], -1)
        
        lr = LinearRegression()
        lr.fit(X_train_flat, y_train)
        
        preds = lr.predict(X_test_flat)
        preds_inv = scaler.inverse_transform(preds)
        y_inv = scaler.inverse_transform(y_test)
        
        mae = mean_absolute_error(y_inv, preds_inv)
        confidence = round(max(50.0, min(99.0, 100 - mae)), 2)
        
        last_real = y_inv[-1][0]
        last_pred = preds_inv[-1][0]
        trend = "UP" if last_pred > last_real else "DOWN"
        
        return {
            "trend": trend,
            "confidence": confidence,
            "note": "Fallback prediction using Scikit-Learn (TensorFlow unavailable on Python 3.14)"
        }

    X, y, scaler = prepare_data(df.values)

    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = build_lstm((X.shape[1], X.shape[2]))
    model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=0)

    preds = model.predict(X_test)

    preds_inv = scaler.inverse_transform(preds)
    y_inv = scaler.inverse_transform(y_test)

    mae = mean_absolute_error(y_inv, preds_inv)
    confidence = round(max(0, 100 - mae), 2)

    # Trend decision
    last_real = y_inv[-1][0]
    last_pred = preds_inv[-1][0]

    trend = "UP" if last_pred > last_real else "DOWN"

    return {
        "trend": trend,
        "confidence": confidence
    }

