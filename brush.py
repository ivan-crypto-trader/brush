import json
import hmac
import base64
import urllib.request
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

user = input("user   : ")
k = open(user+"/API.txt").read().split("\n")

coin = input("symbol : ").upper()
bx_symbol = coin+"-USDT"
bn_symbol = coin+"USDT"

rate = float(input("rate   : "))

APIURL = "https://api-swap-rest.bingbon.pro"
APIKEY = k[0]
SECRETKEY = k[1]


chromedriver_autoinstaller.install()

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--log-level=3')

bn = webdriver.Chrome(options=chrome_options)
bx = webdriver.Chrome(options=chrome_options)

bn.get('https://www.binance.com/zh-TC/futures/'+coin+'USDT')
bx.get('https://swap.bingx.com/zh-tw/'+coin+'-USDT')

os.system("cls")
print("==========================================")
print("user  :", user)
print("coin  :", coin)
print("rate  :", rate)


if True: #setting
        
    def genSignature(path, method, paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        paramsStr = method + path + paramsStr
        return hmac.new(SECRETKEY.encode("utf-8"), paramsStr.encode("utf-8"), digestmod="sha256").digest()

    def post(url, body):
        req = urllib.request.Request(url, data=body.encode("utf-8"), headers={'User-Agent': 'Mozilla/5.0'})
        return urllib.request.urlopen(req).read()

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
        

mode = "no"
roun = 1
order_num = 1
balance = 0
st_balance = 0
amt = 0
st = True
time.sleep(5)

while True:
    bn_price = float(bn.title.split(" ")[0].replace("$", ""))
    bx_price = float(bx.title.split(" ")[0].replace("$", ""))

    if st:
        balance = float(json.loads(get_balance().decode('utf-8'))['data']['account']['balance'])
        set_leverage(symbol=bx_symbol, leverage=int(150/balance*20))
        amt = balance*int(json.loads(get_leverage(symbol=bx_symbol).decode('utf-8'))["data"]["longLeverage"])*0.4/bx_price
        print("==========================================\n")
        print("starting...")
        time.sleep(1)
        print("------------------------------------------")
        print("your balance  :", balance, "\nposition_qty  :", amt)
        print("------------------------------------------")
        st_balance = balance
        st = False
        
    if bn_price < bx_price:
        if roun == 2 and mode == "short":
            mode = "no"
            place_order(symbol=bx_symbol, price=bx_price, action="Open", volume=amt, side="Ask", tradeType="Market")
            print("open short  :", bx_price)
            roun += 1
            time.sleep(60)

        if roun == 4 and mode == "long":
            mode = "no"
            roun = 1
            place_order(symbol=bx_symbol, price=bx_price, action="Close", volume=amt, side="Ask", tradeType="Market")
            print("close short :", bx_price)
            print("-------------------------------")
            balance = json.loads(get_balance().decode('utf-8'))['data']['account']['balance']
            set_leverage(symbol=bx_symbol, leverage=int(150/balance*20))
            amt = balance*int(json.loads(get_leverage(symbol=bx_symbol).decode('utf-8'))["data"]["longLeverage"])*0.4/bx_price
            
            print("balance  :", balance)
            print("earn     :", balance-st_balance)
            st_balance = balance
            print("-------------------------------")

            time.sleep(30)

    if bx_price < bn_price:
        if roun == 2 and mode == "long":
            mode = "no"
            place_order(symbol=bx_symbol, price=bx_price, action="Open", volume=amt, side="Bid", tradeType="Market")
            print("open long   :", bx_price)
            roun += 1
            time.sleep(60)

        if roun == 4 and mode == "short":
            mode = "no"
            roun = 1
            place_order(symbol=bx_symbol, price=bx_price, action="Close", volume=amt, side="Bid", tradeType="Market")
            print("close long  :", bx_price)
            print("-------------------------------")

            balance = json.loads(get_balance().decode('utf-8'))['data']['account']['balance']
            set_leverage(symbol=bx_symbol, leverage=int(150/balance*20))
            amt = balance*int(json.loads(get_leverage(symbol=bx_symbol).decode('utf-8'))["data"]["longLeverage"])*0.4/bx_price

            print("balance  :", balance)
            print("earn     :", balance-st_balance)
            st_balance = balance
            print("-------------------------------")

            time.sleep(30)

    if bn_price > bx_price*(1+rate/100):
        if roun == 1 and mode == "no":
            mode = "short"
            place_order(symbol=bx_symbol, price=bx_price, action="Open", volume=amt, side="Bid", tradeType="Market")
            print("open long   :", bx_price)
            roun += 1

        if roun == 3 and mode == "no":
            mode = "long"
            place_order(symbol=bx_symbol, price=bx_price, action="Close", volume=amt, side="Bid", tradeType="Market")
            print("close long  :", bx_price)
            roun += 1
        
    if bx_price > bn_price*(1+rate/100):
        if roun == 1 and mode == "no":
            mode = "long"
            place_order(symbol=bx_symbol, price=bx_price, action="Open", volume=amt, side="Ask", tradeType="Market")
            print("open short  :", bx_price)
            roun += 1

        if roun == 3 and mode == "no":
            mode = "short"
            place_order(symbol=bx_symbol, price=bx_price, action="Close", volume=amt, side="Ask", tradeType="Market")
            print("close short :", bx_price)
            roun += 1
