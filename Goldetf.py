import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

stock = "TATAGOLD.NS"

data = yf.download(
    stock,
    start="2024-01-01",
    end="2025-01-01",
    progress=False
)

data.reset_index(inplace=True)
data = data[['Date','Close']]
data.dropna(inplace=True)

threshold = 0.002  # 0.2%

data['Return'] = data['Close'].pct_change()

data['Target'] = np.select(
    [
        data['Return'] > threshold,
        data['Return'] < -threshold
    ],
    [2, 0],   # UP=2, DOWN=0
    default=1 # SIDEWAYS=1
)

data.dropna(inplace=True)

scaler = MinMaxScaler()
data['Close_Scaled'] = scaler.fit_transform(data[['Close']])

def create_sequences(X, y, time_steps=30):
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        Xs.append(X[i:i+time_steps])
        ys.append(y[i+time_steps])
    return np.array(Xs), np.array(ys)

X, y = create_sequences(
    data['Close_Scaled'].values,
    data['Target'].values,
    time_steps=30
)

print("X shape:", X.shape)
print("y shape:", y.shape)

split = int(0.8 * len(X))

X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(X_train.shape[1],1)),
    Dropout(0.3),

    LSTM(64),
    Dropout(0.3),

    Dense(3, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

early_stop = EarlyStopping(
    monitor='val_loss',
    patience=5,
    restore_best_weights=True
)

history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=40,
    batch_size=16,
    callbacks=[early_stop],
    verbose=1
)

y_pred_prob = model.predict(X_test)
y_pred = np.argmax(y_pred_prob, axis=1)

print("\n📊 MODEL PERFORMANCE")
print("Accuracy :", accuracy_score(y_test, y_pred))
print("\nConfusion Matrix")
print(confusion_matrix(y_test, y_pred))
print("\nClassification Report")
print(classification_report(y_test, y_pred))

plt.figure(figsize=(12,5))
plt.plot(y_test, label='Actual Trend', alpha=0.7)
plt.plot(y_pred, label='Predicted Trend', alpha=0.7)
plt.yticks([0,1,2], ['DOWN','SIDEWAYS','UP'])
plt.legend()
plt.title("3-Class Trend Prediction")
plt.show()

model.save('goldstock_dl_model.h5')
import joblib
joblib.dump(scaler, 'scaler.pkl')