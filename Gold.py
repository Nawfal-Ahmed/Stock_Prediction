import pandas as pd
import numpy as np
import datetime as dt
import yfinance as yf
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.layers import Dense, Dropout, LSTM
from keras.models import Sequential
stock = "TATAGOLD.NS"
data01 = yf.download(
    "TATAGOLD.NS",
    start="2024-12-31",
    end="2025-12-31",
    group_by=False
)
data01.to_csv("tatagold.csv")
# Flatten columns safely
data01.columns = data01.columns.get_level_values(0)

# Convert index to Date column
data01.reset_index(inplace=True)

print(data01.head())
print(data01.columns)

# Remove first 2 junk rows
data01 = data01.iloc[2:].copy()

# Rename columns correctly
data01.columns = ['Date','Open','High','Low','Close','Volume']

# Convert Date properly
data01['Date'] = pd.to_datetime(data01['Date'])

# Convert numeric columns
cols = ['Open','High','Low','Close','Volume']
data01[cols] = data01[cols].astype(float)

fig = go.Figure(data=[go.Candlestick(
    x=data01['Date'],
    open=data01['Open'],
    high=data01['High'],
    low=data01['Low'],
    close=data01['Close']
)])

fig.update_layout(
    title="TATA Gold ETF Candlestick Chart",
    xaxis_title="Date",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False
)

fig.show()

plt.plot(data01['Close'], label = f'{stock} Closing Price', linewidth = 1)
plt.title(f'{stock} Closing prices over time')
plt.legend()
plt.show()

plt.plot(data01['Open'], label = f'{stock} Openning price', linewidth = 1)
plt.title(f'{stock} Openning prices over time')
plt.legend()
plt.show()

plt.plot(data01['High'], label = f'{stock} High price', linewidth = 1)
plt.title(f'{stock} High prices over time')
plt.legend()
plt.show()

plt.plot(data01['Low'], label = f'{stock} low price', linewidth = 1)
plt.title(f'{stock} Low prices over time')
plt.legend()
plt.show()

temp_data = [10, 20, 30, 40, 50, 60, 70, 80, 90]
print(sum(temp_data[2:7])/5)
df01 = pd.DataFrame(temp_data)
print(df01.rolling(5).mean())
ma100 = data01.Close.rolling(100).mean()
print(ma100)
ma200 = data01.Close.rolling(200).mean()
plt.figure(figsize=(12, 6))
plt.plot(data01.Close, label = f'{stock} Close Price', linewidth = 1)
plt.plot(ma100, label = f'{stock} Moving Average 100 Price', linewidth = 1)
plt.plot(ma200, label = f'{stock} Moving Average 200 Price', linewidth = 1)
plt.legend()
plt.show()
ema100 = data01.Close.ewm(span=100, adjust = False).mean()
ema200 = data01['Close'].ewm(span=200, adjust = False).mean()
plt.figure(figsize=(12, 6))
plt.plot(data01.Close, label = f'{stock} Close Price', linewidth = 1)
plt.plot(ema100, label = f'{stock} Exp. Moving Average 100 Price', linewidth = 1)
plt.plot(ema200, label = f'{stock} Exp. Moving Average 200 Price', linewidth = 1)
plt.legend()
plt.show()

data_training = pd.DataFrame(data01['Close'][0:int(len(data01)*0.70)])
data_testing = pd.DataFrame(data01['Close'][int(len(data01)*0.70): int(len(data01))])
print(data_training.shape)
print(data_testing.shape)
scaler = MinMaxScaler(feature_range = (0, 1))
data_training_array = scaler.fit_transform(data_training)
print(data_training_array)
print(data_training_array.shape[0])
x_train = []
y_train = []

for i in range(100, data_training_array.shape[0]):
    x_train.append(data_training_array[i-100:i])
    y_train.append(data_training_array[i, 0])

x_train, y_train  = np.array(x_train), np.array(y_train)
print(x_train.shape)



model = Sequential()
model.add(LSTM(units = 50, activation = 'relu', return_sequences = True, input_shape = (x_train.shape[1],1)))
model.add(Dropout(0.2))

model.add(LSTM(units = 60, activation = 'relu', return_sequences = True))
model.add(Dropout(0.3))

model.add(LSTM(units = 80, activation = 'relu', return_sequences = True))
model.add(Dropout(0.4))

model.add(LSTM(units = 120, activation = 'relu'))
model.add(Dropout(0.5))

model.add(Dense(units = 1))
print(model.summary())
model.compile(optimizer = 'adam', loss = 'mean_squared_error')
model.fit(x_train, y_train, epochs = 50)
past_100_days = data_training.tail(100)
final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
print(final_df.head())
input_data = scaler.fit_transform(final_df)
x_test = []
y_test = []

for i in range(100, input_data.shape[0]):
    x_test.append(input_data[i-100:i])
    y_test.append(input_data[i, 0])

x_test, y_test  = np.array(x_test), np.array(y_test)
print(x_test.shape)
y_predicted = model.predict(x_test)
print(scaler.scale_)
scaler_factor = 1 / 0.0035166
y_predicted = y_predicted * scaler_factor
print(scaler_factor)
y_test = y_test * scaler_factor
plt.figure(figsize=(12, 6))
plt.plot(y_test, label = 'Original Price', linewidth = 1)
plt.plot(y_predicted, label = 'Predicted Price', linewidth = 1)
plt.legend()
plt.show()
model.save('goldstock_dl_model.h5')