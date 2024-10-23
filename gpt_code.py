import json
import requests
import pandas as pd

URL = "http://fx-trading-game.westeurope.azurecontainer.io:443"
TRADER_ID = "your_trader_id_here"

class Side:
    BUY = "buy"
    SELL = "sell"

# Function to get price history for a product
def get_price_history():
    api_url = URL + "/priceHistory/EURGBP"
    res = requests.get(api_url)
    if res.status_code == 200:
        return json.loads(res.content.decode('utf-8'))["prices"]  # Assuming 'prices' is the key for price history
    return None

# Calculate EMA using pandas
def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

# Function to generate buy/sell signals based on EMA crossovers
def generate_signals(df):
    df['5_ema'] = calculate_ema(df['price'], 5)   # Short-term EMA (5 periods)
    df['20_ema'] = calculate_ema(df['price'], 20) # Longer-term EMA (20 periods)
    
    # Generate buy signal when 5 EMA crosses above 20 EMA
    df['buy_signal'] = (df['5_ema'] > df['20_ema']) & (df['5_ema'].shift(1) <= df['20_ema'].shift(1))
    
    # Generate sell signal when 5 EMA crosses below 20 EMA
    df['sell_signal'] = (df['5_ema'] < df['20_ema']) & (df['5_ema'].shift(1) >= df['20_ema'].shift(1))
    
    return df

# Function to place a trade
def trade(trader_id, qty, side):
    api_url = URL + "/trade/EURGBP"
    data = {"trader_id": trader_id, "quantity": qty, "side": side}
    res = requests.post(api_url, json=data)
    if res.status_code == 200:
        resp_json = json.loads(res.content.decode('utf-8'))
        if resp_json["success"]:
            return resp_json["price"]
    return None

# Main trading logic
def trading_bot():
    price_history = get_price_history()
    if price_history:
        # Convert the price history into a pandas DataFrame
        df = pd.DataFrame(price_history)
        
        # Assuming the response has 'timestamp' and 'price' keys in each record
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Generate buy and sell signals based on EMA crossovers
        df = generate_signals(df)
        
        # Check for buy/sell signals in the latest row
        last_row = df.iloc[-1]
        
        if last_row['buy_signal']:
            print("Buy signal detected. Placing buy order...")
            traded_at = trade(TRADER_ID, 100, Side.BUY)
            if traded_at:
                print(f"Successfully bought at: {traded_at}")
            else:
                print("Buy trade failed.")
        
        elif last_row['sell_signal']:
            print("Sell signal detected. Placing sell order...")
            traded_at = trade(TRADER_ID, 100, Side.SELL)
            if traded_at:
                print(f"Successfully sold at: {traded_at}")
            else:
                print("Sell trade failed.")
        else:
            print("No signal detected. Monitoring continues...")
    else:
        print("Failed to fetch price history.")

if __name__ == '__main__':
    trading_bot()
