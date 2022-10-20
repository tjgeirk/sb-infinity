import datetime
import time

from ccxt import kucoinfutures as kucoin
from pandas import DataFrame as dataframe
from ta import trend, volatility, momentum

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''
COINS = ['ETH', 'BTC']
LOTSPERTRADE = 10
LEVERAGE = 50
TFS = ['5m']

exchange = kucoin({
    'adjustForTimeDifference': True,
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWD
})


def getData(coin, tf):
    data = exchange.fetch_ohlcv(coin, tf, limit=500)
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


def buy(coin, contracts, side):
    print(f'buying {coin}')
    price = exchange.fetch_order_book(coin)['bids'][0][0]
    if side == 'short':
        amount = contracts
        params = {'reduceOnly': True, 'closeOrder': True}
    if side != 'short':
        amount = LOTSPERTRADE
        params = {'leverage': LEVERAGE}
    return exchange.create_limit_buy_order(coin, amount, price, params=params)


def sell(coin, contracts, side):
    print(f'selling {coin}')
    price = exchange.fetch_order_book(coin)['asks'][0][0]
    if side == 'long':
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


def bot(coin, contracts, side):
    o = getData(coin, tf)['open']
    h = getData(coin, tf)['high']
    l = getData(coin, tf)['low']
    c = getData(coin, tf)['close']
    High = h.iloc[-1]
    Low = l.iloc[-1]
    Open = (c.iloc[-2]+o.iloc[-2])/2
    Close = (c.iloc[-1]+h.iloc[-1]+l.iloc[-1])/3

    try:
        if Open > upperband(h, l, c, 20) and Open > Close and rsi(c, 5) < 70:
            sell(coin, contracts, side)

        if Open < lowerband(h, l, c, 20) and Open < Close and rsi(c, 5) > 30:
            buy(coin, contracts, side)

    except Exception as e:
        print(e)


cycle = 0
while True:
    positions = exchange.fetch_positions()
    cycle += 1
    if cycle % 5 == 0:
        exchange.cancel_all_orders()
    for tf in TFS:
        for symbol in COINS:
            coin = str(symbol+'/USDT:USDT')
            if coin not in dict(enumerate(positions)).values():
                contracts = 0
                side = 'none'
                pnl = 0
                bot(coin, contracts, side)
            else:
                for _, v in enumerate(positions):
                    side = v['side']
                    contracts = v['contracts']
                    pnl = v['percentage']
                    bot(coin, contracts, side)
