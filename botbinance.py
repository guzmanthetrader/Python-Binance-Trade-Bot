import talib
import ccxt
import os
from dotenv import load_dotenv
import time

load_dotenv()

BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')

exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY,
    'enableRateLimit': True
})

def get_historical_data(symbol, timeframe):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    ohlcv_data = []
    for candle in ohlcv:
        ohlcv_data.append({
            'timestamp': candle[0],
            'open': candle[1],
            'high': candle[2],
            'low': candle[3],
            'close': candle[4],
            'volume': candle[5]
        })
    return ohlcv_data

def ma_rsi_strategy(ohlcv_data):
    close_prices = [candle['close'] for candle in ohlcv_data]
    ma20 = talib.SMA(close_prices, timeperiod=20)
    ma50 = talib.SMA(close_prices, timeperiod=50)
    rsi = talib.RSI(close_prices, timeperiod=14)

    last_ma20 = ma20[-1]
    last_ma50 = ma50[-1]
    last_rsi = rsi[-1]

    if last_ma20 > last_ma50 and last_rsi > 50:
        return 'buy'
    elif last_ma20 < last_ma50 and last_rsi < 50:
        return 'sell'
    else:
        return None

def execute_trade(symbol, side, quantity, price):
    try:
        order = exchange.create_order(symbol, type='limit', side=side, amount=quantity, price=price)
        print('Trade executed:', order)
    except Exception as e:
        print('Error executing trade:', e)

if __name__ == '__main__':
    symbol = 'BTC/USDT'
    timeframe = '1h'
    risk = 0.01 # riskimiz %1 olarak belirlendi
    take_profit = 1.02 # %2 kar al
    stop_loss = 0.98 # %2 stop loss

    while True:
        try:
            ohlcv_data = get_historical_data(symbol, timeframe)
            trade_signal = ma_rsi_strategy(ohlcv_data)

            if trade_signal == 'buy':
                current_price = exchange.fetch_ticker(symbol)['bid']
                quantity = (risk * exchange.fetch_balance()[symbol.split('/')[1]]['free']) / current_price
                execute_trade(symbol, 'buy', quantity, current_price * take_profit)
                execute_trade(symbol, 'sell', quantity, current_price * stop_loss)
            elif trade_signal == 'sell':
                current_price = exchange.fetch_ticker(symbol)['ask']
                quantity = (risk * exchange.fetch_balance()[symbol.split('/')[0]]['free'])
                execute_trade(symbol, 'sell', quantity, current_price * take_profit)
                execute_trade(symbol, 'buy', quantity, current_price * stop_loss)

            time.sleep(60)
        except Exception as e:
            print('Error occurred:', e)
