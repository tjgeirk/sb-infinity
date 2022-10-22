import datetime
import time
import logging

from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import trend, volatility, momentum

logging.basicConfig(filename='shlongbot7.log',
                    encoding='utf-8', level=logging.DEBUG)

API_KEY = ''
API_SECRET = ''
API_PASSWD = ''
COIN = 'APE'
LOTSPERTRADE = 100
LEVERAGE = 10
TF = '15m'

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
        params = {'reduceOnly': True, 'closeOrder': True}
    if side != 'short':
        amount = LOTSPERTRADE
        params = {'leverage': LEVERAGE}
    return exchange.create_limit_order(coin, 'buy', amount, price, params=params)


def sell():
    print(f'selling {coin}')

    price = exchange.fetch_order_book(coin)['asks'][0][0]
    if side == 'long':
        amount = contracts
        params = {'reduceOnly': True, 'closeOrder': True}
    if side != 'long':
        amount = LOTSPERTRADE
        params = {'leverage': LEVERAGE}

    return exchange.create_limit_order(coin, 'sell', amount, price, params=params)


def ema(ohlc, window, period):
    return trend.ema_indicator(ohlc, window).iloc[-period]


def rsi(ohlc, window, period):
    return momentum.rsi(ohlc, window).iloc[-period]


def bands(ohlc, window, devs, period):
    return {'upper': volatility.bollinger_hband(ohlc, window, devs).iloc[-period], 'lower': volatility.bollinger_lband(ohlc, window, devs).iloc[-period], 'middle': volatility.bollinger_mavg(ohlc, window, devs).iloc[-period]}


logging.info('trader started')

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
        if (Open > lastOpen and Close < lastClose) or (lastOpen < lastClose and Open > Close) and lastClose > bands(c, 20, 1, 2)['upper'] or Close > bands(c, 20, 1, 1)['upper']:
            logging.info(getData(coin, TF)['date'].iloc[-1])
            logging.debug(
                "if (Open > lastOpen and Close < lastClose) or (lastOpen < lastClose and Open > Close) and lastClose > bands(c, 20, 1, 2)['upper''] or Close > bands(c, 20, 1, 1)['upper']:")
            sell()

        if (Open < lastOpen and Close > lastClose) or (lastOpen > lastClose and Open < Close) and lastClose < bands(c, 20, 1, 2)['lower'] or Close < bands(c, 20, 1, 1)['lower']:
            logging.info(getData(coin, TF)['date'].iloc[-1])
            logging.debug(
                "if (Open < lastOpen and Close > lastClose) or (lastOpen > lastClose and Open < Close) and lastClose < bands(c, 20, 1, 2)['lower'] or Close < bands(c, 20, 1, 1)['lower']:")
            buy()

        if side == 'long' and Close < ema(c, 21, 1) < Open:
            logging.info(getData(coin, TF)['date'].iloc[-1])
            logging.debug("if side == 'long' and Close < ema(c, 21, 1)< Open")
            sell()

        if side == 'short' and Close > ema(c, 21, 1) > Open:
            logging.info(getData(coin, TF)['date'].iloc[-1])
            logging.debug(
                "if side == 'short' and Close > ema(c, 21, 1) > Open")
            buy()

        time.sleep(30)

        exchange.cancel_all_orders()
    except Exception as e:
        logging.error(e)
