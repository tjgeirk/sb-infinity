import datetime
import time

from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import trend, volatility, momentum
from pprint import pp

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''
COIN = 'BTC'
LOTSPERTRADE = 1
LEVERAGE = 20
TF = '5m'
STOPLOSS = 0.03
exchange = kcf({
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
        trail = 0
        stop = trail - abs(STOPLOSS)
        params = {'reduceOnly': True, 'closeOrder': True}
    if side != 'short':
        amount = LOTSPERTRADE
        params = {'leverage': LEVERAGE}
    return exchange.create_limit_buy_order(COIN, amount, price, params=params)


def sell():
    print(f'selling {coin}')
    price = exchange.fetch_order_book(coin)['asks'][0][0]
    if side == 'long':
        trail = 0
        stop = trail - abs(STOPLOSS)
        amount = contracts
        params = {'reduceOnly': True, 'closeOrder': True}
    if side != 'long':
        amount = LOTSPERTRADE
        params = {'leverage': LEVERAGE}
    return exchange.create_limit_sell_order(coin, amount, price, params=params)


def ema(pointOfReference, window):
    return trend.ema_indicator(pointOfReference, window).iloc[-1]


def rsi(pointOfReference, window):
    return momentum.rsi(pointOfReference, window).iloc[-1]


def upperband(h, l, c, window):
    return volatility.keltner_channel_hband(h, l, c, window).iloc[-1]


def lowerband(h, l, c, window):
    return volatility.keltner_channel_lband(h, l, c, window).iloc[-1]


cycle = trail = 0
stop = trail - abs(STOPLOSS)
print('trader started')

while True:
    try:
        positions = exchange.fetch_positions()
        cycle += 1
        if cycle % 50 == 0:
            print('clearing queue')
            exchange.cancel_all_orders()
        coin = str(f'{COIN}/USDT:USDT')
        pnl = 0
        contracts = 0
        side = 'none'
        trail = pnl if pnl > trail else trail
        stop = trail - abs(STOPLOSS)
        for i, v in enumerate(positions):
            if v['symbol'] == str(f'{COIN}/USDT:USDT'):
                pnl = v['percentage']
                contracts = v['contracts']
                side = v['side']
                trail = pnl if pnl > trail else trail
                stop = trail - abs(STOPLOSS)
            if pnl < stop and side == 'long':
                sell()
            if pnl < stop and side == 'short':
                buy()

            o = getData(coin, TF)['open']
            h = getData(coin, TF)['high']
            l = getData(coin, TF)['low']
            c = getData(coin, TF)['close']
            High = h.iloc[-1]
            Low = l.iloc[-1]
            Open = (c.iloc[-2]+o.iloc[-2])/2
            Close = (c.iloc[-1]+h.iloc[-1]+l.iloc[-1])/3

            if Open > upperband(h, l, c, 20) and Open > Close and rsi(c, 5) < 70:
                sell()
            if Open < lowerband(h, l, c, 20) and Open < Close and rsi(c, 5) > 30:
                buy()
    except Exception as e:
        time.sleep(10)
        print(e)
