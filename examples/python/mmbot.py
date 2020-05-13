import json
import hashlib
import hmac

import requests as req
import time
import websocket
from threading import Thread
import os
import sys
import traceback
import argparse

from urllib.parse import urlencode
from functools import partial

# region Config
parser = argparse.ArgumentParser(description='Sample Interdax market making bot')
parser.add_argument('-s', '--symbol', help='Instrument to trade (default BTC-PERP)', default="BTC-PERP", type=str)
parser.add_argument('-l', '--leverage', help='Target leverage (default 1)', default=1, type=float)
parser.add_argument('-e', '--environment', help='Environment (test or prod) (default test)', default="test", type=str)
parser.add_argument('-ak', '--api_key', help='API key', type=str)
parser.add_argument('-as', '--api_secret', help='API secret', type=str)
parser.add_argument('-t', '--test', help='Quick test functionality', default=False, action='store_true')
args = parser.parse_args()

if args.environment == "test":
    API_HOST = 'test.interdax.com'
elif args.environment == "prod":
    API_HOST = 'app.interdax.com'
else:
    API_HOST = args.environment

API_KEY_ID = args.api_key
API_KEY_SECRET = args.api_secret
TARGET_SYMBOL = args.symbol
TARGET_LEVERAGE = args.leverage

POSITION_TOLERANCE = 0.3
TARGET_SPREAD = 5e-4
PRICE_TOLERANCE = 3e-4

TEST = args.test
# endregion


def get_headers(path, data_str=""):
    nonce = str(int(time.time() * 1000))
    request = path + data_str + nonce
    hash = hmac.new(bytes(API_KEY_SECRET, 'utf-8'), request.encode('utf-8'), hashlib.sha256).hexdigest()
    return {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'x-itdx-apikey': API_KEY_ID,
        'x-itdx-nonce': nonce,
        'x-itdx-signature': hash,
    }


def get_request_URL(endpoint, params):
    return endpoint + ('?' + urlencode(params) if params else "")


def make_public_request(path, params=None):
    url = get_request_URL(path, params)
    request = req.Request('get', "https://" + API_HOST + url).prepare()
    resp = session.send(request)
    return json.loads(resp.content)


def make_private_request(type, path, params, data):
    url = get_request_URL(path, params)
    data_json = json.dumps(data, separators=(',', ':')) if data else ""
    headers = get_headers(url, data_json)
    request = req.Request(method=type, url="https://" + API_HOST + url, headers=headers, data=data_json).prepare()
    resp = session.send(request)
    if resp.status_code != 200:
        raise Exception(
            "Endpoint " + path + " returned code " + str(resp.status_code) + " with message " + str(resp.content))
    return json.loads(resp.content)


def connect_to_private_ws():
    private_ws = websocket.WebSocketApp("wss://" + API_HOST + "/stream/v1/private",
                                        on_open=on_private_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close,
                                        header=get_headers("/stream/v1/private"))
    p = partial(private_ws.run_forever)
    Thread(target=p).start()


def connect_to_public_ws():
    public_ws = websocket.WebSocketApp("wss://" + API_HOST + "/stream/v1/public",
                                       on_open=on_public_open,
                                       on_message=on_message,
                                       on_error=on_error,
                                       on_close=on_close)
    p = partial(public_ws.run_forever)
    Thread(target=p).start()


def get_summaries():
    summaries = make_public_request('/api/v1/summaries')['summaries']
    return dict([(e['symbol'], e) for e in summaries])


def get_instruments():
    instruments = make_public_request('/api/v1/instruments')['instruments']
    return dict([(e['symbol'], e) for e in instruments])


def get_accounts():
    accounts = make_private_request('get', '/api/v1/accounts', None, None)
    return dict([(e['name'], e) for e in accounts])


def get_margins(account_id=None, asset=None):
    params = {}
    if account_id:
        params['accountId'] = account_id
    if asset:
        params['asset'] = asset
    margins = make_private_request('get', '/api/v1/margins', params, None)['margins']
    return dict([((e['accountId'], e['asset']), e) for e in margins])


def get_position(account_id=None, symbol=None):
    params = {}
    if account_id:
        params['accountId'] = account_id
    if symbol:
        params['symbol'] = symbol
    margins = make_private_request('get', '/api/v1/positions', params, None)['positions']
    return dict([((e['accountId'], e['symbol']), e) for e in margins])


def get_order_history(account_id=None, symbol=None, status=None):
    params = {}
    if account_id:
        params['accountId'] = account_id
    if symbol:
        params['symbol'] = symbol
    if status:
        params['status'] = status
    orders = make_private_request('get', '/api/v1/orders', params, None)['orders']
    return dict([((e['orderId']), e) for e in orders])


def get_orders(account_id=None, symbol=None):
    params = {}
    if account_id:
        params['accountId'] = account_id
    if symbol:
        params['symbol'] = symbol
    params['status'] = "open,partial"
    orders = make_private_request('get', '/api/v1/orders', params, None)['orders']
    return dict([((e['orderId']), e) for e in orders])


def cancel_all(account_id):
    params = {}
    params['accountId'] = account_id
    return make_private_request('delete', '/api/v1/order/all', params, None)


def send_order(account_id, symbol, type, side, qty, px=None, post_only=False):
    data = {'accountId': account_id, 'symbol': symbol, 'orderSide': side, 'orderType': type, 'orderQuantity': str(qty)}
    if px:
        data['limitPrice'] = str(px)
    if post_only:
        data['postOnly'] = post_only
    return make_private_request('post', '/api/v1/order', None, data)['response']


def send_limit_order(account_id, symbol, side, px, qty, post_only=False):
    return send_order(account_id, symbol, "limit", side, qty, px, post_only)


def cancel_by_order_id(order_id):
    params = {}
    params['orderId'] = order_id
    return make_private_request('delete', '/api/v1/order', params, None)


def on_message(ws, msg):
    msgo = json.loads(msg)
    topic = msgo[0]
    content = msgo[1]
    if 'primus::ping' in msg:
        ws.send(msg.replace("ping", "pong"))
    elif "summaries" == topic:
        global summaries
        summaries = dict([(e['symbol'], e) for e in content])
    elif "positions" == topic:
        global positions
        positions = dict([((e['accountId'], e['symbol']), e) for e in content])
    elif "margins" == topic:
        global margins
        margins = dict([((e['accountId'], e['asset']), e) for e in content])
    elif "orders" == topic:
        global orders
        o = content
        if not (o['accountId'] == TARGET_ACCOUNT_ID and o['symbol'] == TARGET_SYMBOL):
            pass  # ignore other orders
        if o['status'] in ('open', 'partial'):
            orders[o['orderId']] = o  # update open order state
        else:
            del orders[o['orderId']]  # delete inactive order


def on_error(ws, error):
    print('ERROR: Websocket' + str(error))

def on_close(ws):
    print('Websocket closed.  Websocket functionality is a critical dependency.  Exiting program ...')
    os._exit(1)


def on_private_open(ws):
    print('Subscribing to private WS topics...')
    ws.send(str('["subscribe", "margins"]'))
    ws.send(str('["subscribe", "positions"]'))
    ws.send(str('["subscribe", "orders"]'))


def on_public_open(ws):
    print('Subscribing to public WS topics...')
    ws.send(str('["subscribe", "summaries"]'))


def rebalance_side(side, orders, balance, position, reference_price):
    side_sign = (1 if side == 'bid' else -1)
    target_position = TARGET_LEVERAGE * (balance * reference_price)
    order_qty = round(min(2 * target_position, max(MIN_QTY, target_position - position * side_sign)))
    order_price = reference_price * (1 - TARGET_SPREAD * side_sign)
    order_already_exists = False
    for o in orders.values():
        if o['orderSide'].lower() != side: continue  # ignore orders from different side
        if (not order_already_exists) and o['orderType'] == 'limit' and order_price / (1 + PRICE_TOLERANCE) < float(
                o['limitPrice']) < order_price * (1 + PRICE_TOLERANCE) and order_qty / (1 + POSITION_TOLERANCE) < int(
            o['leavesQuantity']) < order_qty * (1 + POSITION_TOLERANCE):
            order_already_exists = True  # leave only one order if it's close enough to target one
            continue
        else:
            cancel_by_order_id(o['orderId'])  # cancel all remaining orders
    if not order_already_exists:  # send order if there is not
        send_limit_order(TARGET_ACCOUNT_ID, TARGET_SYMBOL, side, round(order_price / PRICE_INCREMENT) * PRICE_INCREMENT,
                         order_qty)


try:

    print("Initializing...")
    session = req.Session()
    connect_to_private_ws()
    connect_to_public_ws()

    INSTRUMENTS = get_instruments()  # fetch list of instruments

    TARGET_ASSET = INSTRUMENTS[TARGET_SYMBOL]['sellAssetSymbol']
    PRICE_INCREMENT = INSTRUMENTS[TARGET_SYMBOL]['priceIncrement']
    MIN_QTY = INSTRUMENTS[TARGET_SYMBOL]['quantityMin']
    TARGET_ACCOUNT_ID = get_accounts()['Main']['id']  # determine account_id to trade in

    summaries = get_summaries()
    positions = get_position()
    margins = get_margins()
    orders = get_orders(TARGET_ACCOUNT_ID, TARGET_SYMBOL)

    print("Running market-maker loop")

    def make_market():
        try:
            balance = float(margins[(TARGET_ACCOUNT_ID, TARGET_ASSET)]['marketValue'])
            position = int(positions[(TARGET_ACCOUNT_ID, TARGET_SYMBOL)]['quantity'])
            reference_price = float(summaries[TARGET_SYMBOL]['markPrice'])
            rebalance_side('bid', orders.copy(), balance, position, reference_price)
            rebalance_side('ask', orders.copy(), balance, position, reference_price)
        except Exception as e:
            print("Unexpected error:", sys.exc_info()[0], file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        finally:
            time.sleep(2)

    if TEST:
        print('Testing single loop...')
        make_market()
        cancel_all(TARGET_ACCOUNT_ID)
        print('Test passed.  Exiting.')
        os._exit(0)
    else:
        while True:
            make_market()

except KeyboardInterrupt:
    print('Interrupted with keyboard signal')
    os._exit(0)

except Exception as e:
    print("Unexpected error:", sys.exc_info()[0], file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    os._exit(1)
