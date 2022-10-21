import datetime
from pprint import pp
import time
from kucoin import client
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import trend, volatility, momentum

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''
COIN = 'ETH'
LOTSPERTRADE = 100
LEVERAGE = 75
TF = '1m'
STOPLOSS = 0.05
exchange = kcf({
    'adjusTForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})

client = ({
    'adjusTForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})


def getData(coin, TF):
    data = exchange.fetch_ohlcv(coin, TF, limit=500)
    df = {}
    for i, col in enumerate(['date', 'open', 'high', 'low', 'close',
                             'volume']):
        df[col] = []
        for row in data:
            if col == 'date':
                df[col].append(datetime.datetime.fromtimestamp(row[i] / 1000))
            else:
                df[col].append(row[i])
        DF = dataframe(df)
    return DF


def buy():
    print(f'buying {coin}')
    price = exchange.fetch_order_book(coin)['bids'][0][0]
    if side == 'short':
        amount = contracts
        params = {'reduceOnly': True, 'closeOrder': True}
    if side != 'short':
        amount = LOTSPERTRADE
        params = {'leverage': LEVERAGE}
    return exchange.create_stop_limit_order(coin, 'buy', amount, price, (price-(price*abs(STOPLOSS))), params=params)


def sell():
    print(f'selling {coin}')
    price = exchange.fetch_order_book(coin)['asks'][0][0]
    if side == 'long':
        amount = contracts
        params = {'reduceOnly': True, 'closeOrder': True}
    if side != 'long':
        amount = LOTSPERTRADE
        params = {'leverage': LEVERAGE}
    return exchange.create_stop_limit_order(coin, 'sell', amount, price, (price-(price*abs(STOPLOSS))), params=params)


def ema(ohlc, window, period):
    return trend.ema_indicator(ohlc, window).iloc[-period]


def macd(ohlc, fast, slow, signal, period):
    return {'macd': trend.macd(ohlc, slow, fast).iloc[-period], 'signal': trend.macd_signal(ohlc, slow, fast, signal).iloc[-period], 'spread': trend.macd_diff(ohlc, slow, fast, signal).iloc[-period]}


def rsi(ohlc, window, period):
    return momentum.rsi(ohlc, window).iloc[-period]


def bands(ohlc, window, devs, period):
    return {'upper': volatility.bollinger_hband(ohlc, window, devs).iloc[-period], 'lower': volatility.bollinger_lband(ohlc, window, devs).iloc[-period], 'middle': volatility.bollinger_mavg(ohlc, window, devs).iloc[-period]}


def dc(h, l, c, window, period):
    return {'upper': volatility.donchian_channel_hband(h, l, c, window).iloc[-period], 'lower': volatility.donchian_channel_lband(h, l, c, window).iloc[-period], 'middle': volatility.donchian_channel_mband(h, l, c, window).iloc[-period]}


print('trader started')
while True:
    positions = exchange.fetch_positions()
    coin = str(f'{COIN}/USDT:USDT')
    pnl = 0
    contracts = 0
    side = None
    for i, v in enumerate(positions):
        if v['symbol'] == str(f'{COIN}/USDT:USDT'):
            coin = v['symbol']
            pnl = v['percentage']
            contracts = v['contracts']
            side = v['side']
    o = getData(coin, TF)['open']
    h = getData(coin, TF)['high']
    l = getData(coin, TF)['low']
    c = getData(coin, TF)['close']
    Open = (c.iloc[-2]+o.iloc[-2])/2
    lastOpen = (c.iloc[-3]+o.iloc[-3])/2
    Close = (c.iloc[-1]+h.iloc[-1]+l.iloc[-1])/3
    lastClose = (c.iloc[-2]+h.iloc[-2]+l.iloc[-2])/3
    try:
        # if ((l.iloc[-1] < bands(c, 20, 2, 1)['lower']) or (l.iloc[-2] < bands(c, 20, 2, 2)['lower'])) and ((Open < Close) or (Close > lastClose and Open < lastOpen)):buy()

        # if ((h.iloc[-1] > bands(c, 20, 2, 1)['upper']) or (h.iloc[-2] > bands(c, 20, 2, 2)['upper'])) and ((Open > Close) or (Close < lastClose and Open > lastOpen)):sell()

        # if side == 'long' and Open > bands(c, 20, 2, 1)['middle'] > Close:sell()

        # if side == 'short' and Open < bands(c, 20, 2, 1)['middle'] < Close:buy()

        #if dc(h, l, c, 20, 2)['lower'] == l.iloc[-2] and c.iloc[-2] > l.iloc[-2] and rsi(c, 5, 2) < 10 and rsi(c, 5, 1) > rsi(c, 5, 2) and Open < Close:buy()

        #if dc(h, l, c, 20, 2)['upper'] == h.iloc[-2] and c.iloc[-2] < h.iloc[-2] and rsi(c, 5, 2) > 90 and rsi(c, 5, 1) < rsi(c, 5, 2) and Open > Close:sell()

        if rsi(c, 8, 1) > rsi(c, 8, 2) < 30 and ema(o, 3, 1) < ema(c, 3, 1) and (Close > lastClose or Close > Open):
            buy()

        if rsi(c, 8, 1) < rsi(c, 8, 2) > 70 and ema(o, 3, 1) > ema(c, 3, 1) and (Close < lastClose or Close < Open):
            sell()

        if 30 < rsi(c, 8, 1) < 70:

            if ema(o, 3, 1) < ema(c, 3, 1) and Open < Close:
                buy()

            elif ema(o, 3, 1) > ema(c, 3, 1) and Open > Close:
                sell()

        time.sleep(5)

    except Exception as e:
        print(e)
