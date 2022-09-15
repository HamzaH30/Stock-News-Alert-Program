import os
import requests
import datetime
from twilio.rest import Client

STOCK = "TSLA"
COMPANY_NAME = "Tesla"
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"


def previous_weekday(date):
    """Takes in a date, and returns the previous weekday of that date."""
    date -= datetime.timedelta(days=1)
    # If the day is Saturday or Sunday, then continue subtracting until it's a weekday (Friday)
    while date.weekday() > 4:
        date -= datetime.timedelta(days=1)
    return date


def calculate_stock_price_change(type_of_output: int):
    """
    If the parameter passed in is:\n
    0 - Returns whether the stock price changed by 5%\n
    1 - Returns if price increased or decreased, and the amount at which it did
    """
    # GET request to Alpha Vantage API (stock API)
    stock_api_parameters = {
        "apikey": os.environ.get("ALPHA_VANTAGE_API_KEY"),
        "function": "TIME_SERIES_DAILY",
        "symbol": STOCK,
    }
    response = requests.get(STOCK_ENDPOINT, params=stock_api_parameters)
    response.raise_for_status()
    stock_data = response.json()["Time Series (Daily)"]

    # The closing prices of yesterday's and the day before yesterday's stock prices
    last_weekday_closing_price = float(stock_data[str(last_weekday)]["4. close"])
    second_last_weekday_closing_price = float(stock_data[str(second_last_weekday)]["4. close"])

    stock_price_difference = last_weekday_closing_price - second_last_weekday_closing_price
    if type_of_output == 0:
        # Return True if there stock price changed by 5%
        return abs(stock_price_difference) >= round(0.05 * last_weekday_closing_price, 2)
    else:
        if stock_price_difference > 0:
            return "🔺"
        else:
            return "🔻"


def get_articles() -> list[dict, dict, dict]:
    news_api_parameters = {
        "apiKey": os.environ.get("NEWS_API_KEY"),
        "qInTitle": COMPANY_NAME,
        "from": last_weekday,
        "to": second_last_weekday,
        "sortBy": "popularity",
    }
    response = requests.get(NEWS_ENDPOINT, params=news_api_parameters)
    response.raise_for_status()
    # return the first 3 articles
    return response.json()["articles"][:3]


def send_sms():
    text_to_send = ""
    for article in articles:
        text_to_send += f"Headline: {article['title']}\nBrief: {article['description']}\n\n"

    account_SID = os.environ.get("TWILLIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILLIO_AUTH_TOKEN")
    client = Client(account_SID, auth_token)

    message = client.messages.create(
        body=f"{STOCK} PRICE CHANGE by {calculate_stock_price_change(1)} 5%!\n\n{text_to_send}",
        from_=TWILIO_PHONE_NUMBER,
        to="15146998167"
    )


# The previous and "day before previous" workdays
last_weekday = previous_weekday(datetime.datetime.now()).date()
second_last_weekday = previous_weekday(last_weekday)

# When STOCK price increase/decreases by 5% between yesterday and the day before yesterday
if calculate_stock_price_change(0):
    # Fetch the first 3 articles for the COMPANY_NAME.
    articles = get_articles()
    # send SMS
    send_sms()
