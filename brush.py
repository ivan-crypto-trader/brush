import time
import os
import json
import hmac
import base64
import urllib.request
import urllib3
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def wait_for_internet_connection():
    while True:
        try:
            urllib3.urlopen('https://www.google.com.tw/',timeout=1)
            return
        except urllib3.URLError:
            time.sleep(3)

print("Internet connection successful !!!")

url = 'https://raw.githubusercontent.com/ivan-crypto-trader/brush/main/setting.txt'
response = requests.get(url)
setting = response.text.split("\n")

APIURL = "https://api-swap-rest.bingbon.pro"
APIKEY = setting[0].split()[-1]
SECRETKEY = setting[1].split()[-1]

coin = setting[2].split()[-1].upper()
bx_symbol = coin+"-USDT"
bn_symbol = coin+"USDT"

rate = float(setting[3].split()[-1])

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--log-level=3')
bx = webdriver.Chrome(options=chrome_options)
bn = webdriver.Chrome(options=chrome_options)

bx.get('https://swap.bingx.com/zh-tw/'+coin+'-USDT')

mode = "no"

                
if True: #setting
        
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
        post(url, paramsStr)

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

balance = get_balance()["data"]["account"]["balance"]

def print_info():
    os.system("cls")
    print("--------------------------------------")
    print("coin       :", coin)
    print("rate       :", rate)
    print("price mode :", setting[4].split()[-1])
    print("balance    :", balance)
    print("--------------------------------------")
    time.sleep(3)

time.sleep(3)
if setting[4].split()[-1] == "f":
    bx_price = float(bx.title.split(" ")[0][1:])
    bn.get('https://www.binance.com/zh-TC/futures/'+coin+'USDT')
    print_info()
    amt = balance*get_leverage(symbol=bx_symbol)["data"]["longLeverage"]*0.9/bx_price
    
elif setting[4].split()[-1] == "s":
    bx_price = float(bx.title.split(" ")[0][1:])
    bn.get('https://www.binance.com/zh-TC/trade/'+coin+'_USDT')
    print_info()
    amt = balance*get_leverage(symbol=bx_symbol)["data"]["longLeverage"]*0.9/bx_price
        
else:
    print("price mode error !")
    exit()

           
while True:
    try:
        bn_price = float(bn.title.split()[0])
        bx_price = float(bx.title.split(" ")[0][1:])
        if bn_price < bx_price and mode == "long":

            if place_order(symbol=bx_symbol, price=bx_price, action="Close", volume=amt, side="Ask", tradeType="Market")["code"] == 0:
                mode = "no"
                print("close long  :", bx_price)
                balance = get_balance()["data"]["account"]["balance"]
                print("--------------------------------------")
                print("balance     :", balance)
                amt = balance*get_leverage(symbol=bx_symbol).decode("UTF-8")["data"]["longLeverage"]*0.9/bx_price

        if bx_price < bn_price and mode == "short":
            if place_order(symbol=bx_symbol, price=bx_price, action="Close", volume=amt, side="Bid", tradeType="Market")["code"] == 0:
                mode = "no"
                print("close short :", bx_price)
                balance = get_balance()["data"]["account"]["balance"]
                print("--------------------------------------")
                print("balance     :", balance)
                amt = balance*get_leverage(symbol=bx_symbol)["data"]["longLeverage"]*0.9/bx_price


        if bn_price > bx_price*(1+rate/100) and mode == "no":
            if place_order(symbol=bx_symbol, price=bx_price, action="Open", volume=amt, side="Bid", tradeType="Market")["code"] == 0:
                mode = "long"
                print("======================================")
                print("open long   :", bx_price)
            else:
                balance = get_balance()["data"]["account"]["balance"]
                amt = balance*get_leverage(symbol=bx_symbol)["data"]["longLeverage"]*0.9/bx_price
                print("error")

        if bx_price > bn_price*(1+rate/100) and mode == "no":
            if place_order(symbol=bx_symbol, price=bx_price, action="Open", volume=amt, side="Ask", tradeType="Market")["code"] == 0:
                mode = "short"
                print("======================================")
                print("open short  :", bx_price)
            else:
                balance = get_balance()["data"]["account"]["balance"]
                amt = balance*get_leverage(symbol=bx_symbol)["data"]["longLeverage"]*0.9/bx_price
                print("error")
    except:
        pass

