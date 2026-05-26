# Stock Predictor

Stock Predictor is a web application designed to forecast stock and ETF trends. The application combines a Django-based web interface with machine learning models to analyze historical stock data and predict future price movements.

## Deployment Link
You can access the live web application here:
https://stock-prediction-q2lt.onrender.com/dashboard/

## Project Overview
The Stock Predictor application allows users to forecast trends for key financial assets, focusing primarily on high-volume Indian stocks and gold exchange-traded funds (ETFs) such as POWERGRID.NS and TATAGOLD.NS.

Key Features:
* Dashboard containing wallet balance, portfolio value, and a list of recent predictions.
* Watchlist to pin, monitor, and update target alerts for individual stock tickers.
* Quick Predict interface to run forecasts on-demand for specific time ranges.
* History tracker that catalogs all past predictions, their confidence levels, and predicted trends.
* Automated chart visualization and technical analysis metadata.

## Machine Learning Framework
The prediction engine uses a dual-layered approach to ensure reliability across all environments:
1. Deep Learning Model (Primary): A long short-term memory (LSTM) neural network model trained using Keras/TensorFlow. It processes sequence data to predict future price trends.
2. Machine Learning Fallback (Alternative): If TensorFlow is not supported in the host environment (such as on Python 3.14 or light cloud environments like Render), the system automatically falls back to an advanced Random Forest Regressor. 

The Random Forest model utilizes a 10-day rolling lag window to map historical close price sequences to the next day's price, capturing non-linear relationships without needing complex data scaling.

## Project Structure
The repository is organized as follows:
* stockpredictor/ - Core Django project directory.
  * stockpredictor/ - Configuration, routing, and settings.
  * prediction/ - Django application containing models, views, templates, forms, and core prediction logic.
    * templates/ - HTML templates for the frontend interface.
    * models.py - Database schemas for stock predictions, watchlist items, and profiles.
    * views.py - Controller endpoints for historical charts, watchlists, and prediction views.
    * utils.py - Core ML forecasting and data download helper functions.
  * ml_models/ - Saved LSTM weights and scaling artifacts.
* requirements.txt - Software dependencies.

## Technical Enhancements Made
* Smart Symbol Fallback: The data fetcher automatically appends exchange suffixes (e.g. .NS) for NSE stocks when the user inputs plain text tickers (e.g. POWERGRID), preventing failure on Yahoo Finance downloads.
* ForeignKey Integrity: Predictions are successfully associated with verified StockInfo entries upon creation, and the string representation method has been patched to prevent AttributeError crashes.
* Interactive Select Dropdown: The Quick Predict form is restricted to existing ETFs/stocks with pre-trained models to ensure valid inputs.
* Date Fields Bugfix: Corrected the form field attributes in the dashboard template to properly map to the Django form validator.

## Local Installation Guide
Follow these steps to run the application locally:

1. Clone the repository:
   git clone https://github.com/Nawfal-Ahmed/Stock_Prediction.git
   cd Stock_Prediction

2. Create and activate a virtual environment:
   python -m venv .venv
   source .venv/bin/activate  # On Linux/macOS
   .venv\Scripts\activate     # On Windows

3. Install the dependencies:
   pip install -r stockpredictor/requirements.txt

4. Run database migrations:
   cd stockpredictor
   python manage.py migrate

5. Launch the development server:
   python manage.py runserver

6. Open your web browser and navigate to:
   http://127.0.0.1:8000/
