import datetime
import time

from ccxt import kucoinfutures as kucoin
from pandas import DataFrame as dataframe
from ta import trend, volatility, momentum
from pprint import pp

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''
COINS = ['ETH', 'BTC']
LOTSPERTRADE = 10
LEVERAGE = 50
TF = '5m'
STOPLOSS = 0.1
TAKEPROFIT = 0.1
exchange = kucoin({
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
    o = getData(coin, TF)['open']
    h = getData(coin, TF)['high']
    l = getData(coin, TF)['low']
    c = getData(coin, TF)['close']
    High = h.iloc[-1]
    Low = l.iloc[-1]
    Open = (c.iloc[-2]+o.iloc[-2])/2
    Close = (c.iloc[-1]+h.iloc[-1]+l.iloc[-1])/3

    try:
        if crypto['pnl'] < -abs(crypto['stop']) or crypto['pnl'] > TAKEPROFIT:
            sell(coin, contracts, side) if side == 'long' else buy(
                coin, contracts, side)

        if Open > upperband(h, l, c, 20) and Open > Close and rsi(c, 5) < 70:
            sell(coin, contracts, side)

        if Open < lowerband(h, l, c, 20) and Open < Close and rsi(c, 5) > 30:
            buy(coin, contracts, side)

    except Exception as e:
        print(e)


cycle = 0
coin = {}
for symbol in COINS:
    coin[symbol] = {'symbol': str(f'{symbol}/USDT:USDT'), 'side': 'none',
                    'contracts': 0, 'pnl': 0, 'trail': 0, 'stop': -abs(STOPLOSS)}
while True:
    positions = exchange.fetch_positions()
    for symbol in COINS:
        crypto = coin[symbol]
        cycle += 1
        if cycle % 50 == 0:
            print('still running :) -- clearing queue')
            exchange.cancel_all_orders(crypto['symbol'])
        for i, v in enumerate(positions):
            if v['symbol'] == crypto['symbol']:
                crypto.update({'pnl': v['percentage']})
                crypto.update({'contracts': v['contracts']})
                crypto.update({'side': v['side']})
            if v['percentage'] > crypto['trail']:
                crypto.update({'trail': v['percentage']})
                crypto.update({'stop': (crypto['trail']-abs(STOPLOSS))})
            if crypto['pnl'] <= crypto['stop']:
                if crypto['side'] == 'long':
                    sell(getData(crypto['symbol'], TF)['close'].iloc[-1])
                if crypto['side'] == 'short':
                    buy(getData(crypto['symbol'], TF)['close'].iloc[-1])
        
        bot(crypto['symbol'], crypto['contracts'], crypto['side'])
