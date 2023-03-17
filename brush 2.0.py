import time
import os
import json
import hmac
import base64
import urllib.request
import urllib3
import websocket
import requests
import threading

def wait_for_internet_connection():
    while True:
        try:
            urllib3.urlopen('https://www.google.com.tw/',timeout=1)
            return
        except urllib3.URLError:
            time.sleep(3)

print("Internet connection successful !!!")

setting = open(input("user : ")+"/setting.txt").read().split("\n")

APIURL = "https://api-swap-rest.bingbon.pro"
APIKEY = setting[0].split()[-1]
SECRETKEY = setting[1].split()[-1]

coin = setting[2].split()[-1].upper()
bx_symbol = coin+"-USDT"
bn_symbol = coin+"USDT"

rate = float(setting[3].split()[-1])
                
def Setting():
    global genSignature
    global post
    global get_balance
    global get_price
    global place_order
    global set_leverage
    global get_leverage

    def genSignature(path, method, paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        paramsStr = method + path + paramsStr
        return hmac.new(SECRETKEY.encode("utf-8"), paramsStr.encode("utf-8"), digestmod="sha256").digest()

    def post(url, body):
        req = urllib.request.Request(url, data=body.encode("utf-8"), headers={'User-Agent': 'Mozilla/5.0'})
        return json.loads(urllib.request.urlopen(req).read().decode("UTF-8").replace("'", '"'))

    def get_balance():
        paramsMap = {
            "apiKey": APIKEY,
            "timestamp": int(time.time()*1000),
            "currency": "USDT",
        }
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        paramsStr += "&sign=" + urllib.parse.quote(base64.b64encode(genSignature("/api/v1/user/getBalance", "POST", paramsMap)))
        url = "%s/api/v1/user/getBalance" % APIURL
        return post(url, paramsStr)

    def get_price(symbol):
        return requests.get("https://api-swap-rest.bingbon.pro/api/v1/market/getLatestPrice?symbol="+symbol).json()

    def place_order(symbol, side, price, volume, tradeType, action):
        paramsMap = {
            "symbol": symbol,
            "apiKey": APIKEY,
            "side": side,
            "entrustPrice": price,
            "entrustVolume": volume,
            "tradeType": tradeType,
            "action": action,
            "timestamp": int(time.time()*1000),
        }
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        paramsStr += "&sign=" + urllib.parse.quote(base64.b64encode(genSignature("/api/v1/user/trade", "POST", paramsMap)))
        url = "%s/api/v1/user/trade" % APIURL
        return post(url, paramsStr)
    
    def set_leverage(symbol, leverage):
        paramsMap = {
            "symbol": symbol,
            "apiKey": APIKEY,
            "side": "Long",
            "leverage": leverage,
            "timestamp": int(time.time()*1000),
        }
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        paramsStr += "&sign=" + urllib.parse.quote(base64.b64encode(genSignature("/api/v1/user/setLeverage", "POST", paramsMap)))
        url = "%s/api/v1/user/setLeverage" % APIURL
        post(url, paramsStr)

        paramsMap = {
            "symbol": symbol,
            "apiKey": APIKEY,
            "side": "Short",
            "leverage": leverage,
            "timestamp": int(time.time()*1000),
        }
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        paramsStr += "&sign=" + urllib.parse.quote(base64.b64encode(genSignature("/api/v1/user/setLeverage", "POST", paramsMap)))
        url = "%s/api/v1/user/setLeverage" % APIURL
        return post(url, paramsStr)

    def get_leverage(symbol):
        paramsMap = {
            "symbol": symbol,
            "apiKey": APIKEY,
            "timestamp": int(time.time()*1000),
        }
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        paramsStr += "&sign=" + urllib.parse.quote(base64.b64encode(genSignature("/api/v1/user/getLeverage", "POST", paramsMap)))
        url = "%s/api/v1/user/getLeverage" % APIURL
        return post(url, paramsStr)

bn_price = 0
fs = ""

if setting[4].split()[-1] == "f":
    fs = "f"

def on_message(ws, message):
    global bn_price
    data = json.loads(message)
    if data['e'] == 'trade':
        bn_price = float(data['p'])

def run_trade():
    Setting()
    balance = get_balance()["data"]["account"]["balance"]
    def print_info():
        os.system("cls")
        print("--------------------------------------")
        print("coin       :", coin)
        print("rate       :", rate)
        print("price mode :", setting[4].split()[-1])
        print("balance    :", balance)
        print("--------------------------------------")
    #time.sleep(1000)
    print_info()
    
    x = 0.9
    amt_error = 0
    mode = "no"

    leverage = get_leverage(symbol=bx_symbol)["data"]["longLeverage"]
    bx_price = float(get_price(bx_symbol)['data']['tradePrice'])
    amt = balance*leverage*x/bx_price

    while bn_price == 0:
        pass

    print("start !!!")

    while True:
        time.sleep(0.1)
        try:
            bx_price = float(get_price(bx_symbol)['data']['tradePrice'])
            if bn_price < bx_price and mode == "long":
                if place_order(symbol=bx_symbol, price=bx_price, action="Close", volume=amt, side="Ask", tradeType="Market")["code"] == 0:
                    mode = "no"
                    print("close long  :", bx_price)
                    balance = get_balance()["data"]["account"]["balance"]
                    print("--------------------------------------")
                    print("balance     :", balance)
                    x *= 1.01
                    amt = balance*get_leverage(symbol=bx_symbol).decode("UTF-8")["data"]["longLeverage"]*x/bx_price

            if bx_price < bn_price and mode == "short":
                if place_order(symbol=bx_symbol, price=bx_price, action="Close", volume=amt, side="Bid", tradeType="Market")["code"] == 0:
                    mode = "no"
                    print("close short :", bx_price)
                    balance = get_balance()["data"]["account"]["balance"]
                    print("--------------------------------------")
                    print("balance     :", balance)
                    x *= 1.01
                    amt = balance*get_leverage(symbol=bx_symbol)["data"]["longLeverage"]*x/bx_price


            if bn_price > bx_price*(1+rate/100) and mode == "no":
                if place_order(symbol=bx_symbol, price=bx_price, action="Open", volume=amt, side="Bid", tradeType="Market")["code"] == 0:
                    amt_error = 0
                    mode = "long"
                    print("======================================")
                    print("open long   :", bx_price)
                else:
                    balance = get_balance()["data"]["account"]["balance"]
                    leverage = get_leverage(symbol=bx_symbol)["data"]["longLeverage"]
                    amt = balance*leverage*x/bx_price
                    print("amt error")
                    amt_error += 1
                    
            if bx_price > bn_price*(1+rate/100) and mode == "no":
                if place_order(symbol=bx_symbol, price=bx_price, action="Open", volume=amt, side="Ask", tradeType="Market")["code"] == 0:
                    amt_error = 0
                    mode = "short"
                    print("======================================")
                    print("open short  :", bx_price)
                else:
                    balance = get_balance()["data"]["account"]["balance"]
                    leverage = get_leverage(symbol=bx_symbol)["data"]["longLeverage"]
                    amt = balance*leverage*x/bx_price
                    print("amt error")
                    amt_error += 1

            if amt_error >= 2:
                x *= 0.9
                amt = balance*leverage*x/bx_price
                amt_error = 0
        except:
            pass
        

threading.Thread(target=run_trade).start()
if bn_symbol == "LUNAUSDT":
    bn_symbol = "LUNA2USDT"
ws = websocket.WebSocketApp("wss://"+fs+"stream.binance.com/ws/"+bn_symbol.lower()+"@trade", on_message=on_message)
ws.run_forever()
