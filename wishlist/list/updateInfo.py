from ast import parse
from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
import base64
import json
import requests
import re
import aiohttp
import asyncio
import platform

if platform.system()=='Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def requestURL(url):
    header = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    try:
        req = requests.get(url, headers=header, cookies={"AUTH_ADULT" : "1"})
        if(req.status_code == 404):
            return {"success" : False, "error" : "404 Status Code"}
    except Exception as err:
        print(f"Invalid url: {url}")
        print(err)
        return {"success" : False, "error" : "Exception in requestURL"}
    else:
        return {"success" : True, "req":req}

def requestAitaikuji(url):
    try:
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
        options.set_capability("pageLoadStrategy", "eager")
        driver = webdriver.Firefox(options=options)
        driver.get(url)
        html = driver.page_source
    except:
        print(f"Invalid url: {url}")
        return {"success" : False}
    else:
        return {"success" : True, "req":html}
    finally:
        driver.quit()

def extractOrigin(url):     #Can return None if no match
    m = re.search(r"^(https://)?(www\.)?(\S+?)\.(com|co\.jp|jp|pm)", url)

    if m is None:
        return "N/A"

    res = m.group(3)
    if(res.find("booth") < 0):
        return res
    else:
        return "booth"              #To account for username.booth for booth sites    

#Scraping info from otaku republic and sister sites
def otakuRepublicScrape(html):
    metaTags = SoupStrainer("meta")
    soup = BeautifulSoup(html, "html.parser", parse_only=metaTags)
    if(soup.find("meta", property="og:type")["content"] != "product"):
        return {"success" : False, "msg" : "Not a republic product page"}

    # Scraping info from the meta tags
    res = {}
    res["url"] = soup.find("meta", property="og:url")["content"]
    res["price"] = float(soup.find("meta", property="og:price:amount")["content"])
    res["currency"] = soup.find("meta", property="og:price:currency")["content"]
    if(soup.find("meta", property="og:availability")["content"] == "instock"):      #preorders are also listed as instock
        res["inStock"] = True
    else:
        res["inStock"] = False

    res["origin"] = "Republic"
    
    return {"success" : True, "res" : res}

#Scraping info from CDJapan
def cdJapanScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    res = {}
    res["url"] = soup.find("meta", property="og:url")["content"]
    #Checking if the url is a product page
    if(res["url"].find("cdjapan.co.jp/product/") < 0):
        return {"success" : False, "msg" : "Not a CDJapan product page"}

    res["price"] = float(soup.find("span", itemprop="price")["content"])
    res["currency"] = "JPY"
    if(soup.find("a", href="https://www.cdjapan.co.jp/guide/help/shipping/when_will_my_order_ship").get_text().strip() == "Sold Out"):
        res["inStock"] = False
    else:
        res["inStock"] = True

    res["origin"] = "CDJapan"
    
    return {"success" : True, "res" : res}

#Scraping info from Aitaikuji
def aitaikujiScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    res = {}
    temp = soup.find("meta", property="og:type")
    #Cheking if url is product page
    if(temp is None or temp["content"] != "og:product"):
        return {"success" : False, "msg" : "Not a aitaikuji product page"}

    res["url"] = soup.find("meta", property="og:url")["content"]
    res["price"] = float(soup.find("meta", property="product:price:amount")["content"])
    res["currency"] = soup.find("meta", property="product:price:currency")["content"]
    if(soup.find("div", title="Availability")["class"][1] == "available"):
        res["inStock"] = True
    else:
        res["inStock"] = False

    res["origin"] = "Aitaikuji"

    return {"success" : True, "res" : res}

#Scraping info from Etsy (Doesn't work well with options + out of stock)
def etsyScrape(html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("script"))
    infoJSON = soup.find("script", type="application/ld+json")

    if(infoJSON is None):
        return {"success" : False, "msg" : "Not an etsy product page"}
        
    infoJSON = json.loads(infoJSON.get_text())
    res = {}
    res["url"] = infoJSON["url"]
    if("highPrice" in infoJSON["offers"].keys()):
        res["price"] = float(infoJSON["offers"]["highPrice"])
    else:
        res["price"] = float(infoJSON["offers"]["price"])
    res["currency"] = infoJSON["offers"]["priceCurrency"]
    res["inStock"] =  (infoJSON["offers"]["availability"] == "https://schema.org/InStock")

    res["origin"] = "Etsy"

    return {"success" : True, "res" : res}

#Scraping info from omocat
def omocatScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    #check if product page
    if(soup.find("meta", property="og:type")["content"] != "product"):
        return {"success" : False, "msg" : "Not a omocat product page"}
    
    res = {}
    infoJSON = soup.find("script", class_="product-json").get_text()
    infoJSON = json.loads(infoJSON)
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("meta"))
    res["url"] = soup.find("meta", property="og:url")["content"]
    res["price"] = float(soup.find("meta", property="og:price:amount")["content"])
    res["currency"] = soup.find("meta", property="og:price:currency")["content"]
    res["inStock"] = infoJSON["available"]

    res["origin"] = "Omocat"

    return {"success" : True, "res" : res}

#Scraping info from the crunchyroll store
def crunchyrollScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    #check if product page
    infoJSON = soup.find("div", class_="product-detail")
    if(infoJSON is None):
        return {"success" : False, "msg" : "Not a crunchyroll product page"}

    infoJSON = infoJSON["data-segmentdata"]    
    infoJSON = json.loads(infoJSON)

    res= {}
    res["url"] = infoJSON["url"]
    res["price"] = float(infoJSON["price"])
    res["currency"] = infoJSON["currency"]
    if(soup.find("div", class_="availability")["data-available"] == "true"):
        res["inStock"] = True
    else:
        res["inStock"] = False

    res["origin"] = "Crunchyroll"

    return {"success" : True, "res" : res}

def melonbooksScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    #check if product page
    res={}
    res["url"] = soup.find("link", rel="canonical")["href"]
    if(res["url"].find("melonbooks.co.jp/detail/") < 0):
        return {"success" : False, "msg" : "Not a melonbook product page"}

    res["price"] = float(soup.find("span", class_="yen").get_text().strip().removeprefix("¥"))
    res["currency"] = "JPY"
    if(soup.find("span", class_="state-instock").get_text() == "-"):
        res["inStock"] = False
    else:
        res["inStock"] = True

    res["origin"] = "Melonbooks"

    return {"success" : True, "res" : res}

def goodsmileshopScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    # Check if product page
    url = soup.find("meta", property="og:url")
    if(url is None):
        return {"success" : False, "msg" : "Not a good smile product page"}

    # Info
    res = {}
    res = {"url" : url["content"].replace("http://ap-com.gsls", "https://goodsmileshop.com")}
    res["price"] = float(soup.find("div", class_="big-price").get_text(strip=True).removeprefix("¥").replace(",", ""))
    res["currency"] = "JPY"
    stock = soup.find("div", class_="qty").span
    if(stock.get_text(strip=True) == "Out of Stock"):
        res["inStock"] = False
    else:
        res["inStock"] = True

    res["origin"] = "GoodSmile"

    return {"success" : True, "res" : res}

def goodsmileScrape(html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("script"))

    # Check if product page
    info = soup.find("script", type="application/ld+json")
    if(info is None):
        return {"success" : False, "msg" : "Not a good smile product page"}

    # Info
    info = json.loads(info.get_text())
    res={}
    res["url"] = info["url"]
    res["price"] = float(info["offers"]["price"])
    res["currency"] = info["offers"]["priceCurrency"]
    if("availability" in info["offers"]):
        res["inStock"] = True
    else:
        res["inStock"] = False

    res["origin"] = "GoodSmile"

    return {"success" : True, "res" : res}

def hobbygenkiScrape(html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("meta"))

    # Check if product page
    url = soup.find("meta", property = "og:url")
    if(url is None):
        return {"success" : False, "msg" : "Not a hobbygenki product page"}

    # Info
    res = {"url" : url["content"]}
    res["price"] = float(soup.find("meta", property = "product:price:amount")["content"])
    res["currency"] = soup.find("meta", property = "product:price:currency")["content"]
    if(soup.find("meta", property = "product:availability")["content"] == "in stock"):
        res["inStock"] = True
    else:
        res["inStock"] = False

    res["origin"] = "Hobby Genki"

    return {"success" : True, "res" : res}

def solarisjapanScrape(html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("meta"))

    # Check if product page
    if(soup.find("meta", property = "og:type")["content"] != "product"):
        return {"success" : False, "msg" : "Not a solaris japan product page"}

    # Info
    res = {}
    res["url"] = soup.find("meta", property = "og:url")["content"]
    res["price"] = float(soup.find("meta", property = "og:price:amount")["content"].replace(",", ""))
    res["currency"] = soup.find("meta", property = "og:price:currency")["content"]
    if(res["price"] == 0):
        res["inStock"] = False
    else:
        res["inStock"] = True

    res["origin"] = "Solaris Japan"

    return {"success" : True, "res" : res}

def toranoanaScrape(html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("script"))

    # Check if product page
    info = soup.find("script", type="application/ld+json", string = re.compile("Product"))

    if (info is None):
        return {"success" : False, "msg" : "Not a toranora product page"}
    info = json.loads(info.get_text())
    # Info
    res = {}
    res["url"] = info["offers"]["url"]
    res["price"] = float(info["offers"]["price"])
    res["currency"] = info["offers"]["priceCurrency"]
    if(info["offers"]["availability"] == "https://schema.org/SoldOut"):
        res["inStock"] = False
    else:
        res["inStock"] = True

    res["origin"] = "Toranoana"

    return {"success" : True, "res" : res}

def hljScrape(html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("script"))

    # Check if product page
    info = soup.find("script", type = "application/ld+json")
    if(info is None):
        return {"success" : False, "msg" : "Not a hlj product page"}

    # Info
    info = json.loads(info.get_text())
    res = {}
    res["url"] = info["offers"]["url"]
    res["price"] = float(info["offers"]["price"])
    res["currency"] = info["offers"]["priceCurrency"]
    if((info["offers"]["availability"] == "https://schema.org/InStock") or (info["offers"]["availability"] == "https://schema.org/PreOrder")):
        res["inStock"] = True
    else:
        res["inStock"] = False

    res["origin"] = "HobbyLink Japan"

    return {"success" : True, "res" : res}

def dlsiteScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    # Check if Product page
    url = soup.find("meta", property="og:url")
    if(url is None):
        return {"success" : False, "msg" : "Not a dlsite product page"}

    # Info
    info = soup.find("div", attrs={"data-price" : True})
    res = {}
    res["url"] = url["content"]
    res["price"] = float(info["data-price"])
    res["currency"] = "JPY"
    res["inStock"] = True                   #Digital item so always true

    res["origin"] = "DLSite"

    return {"success" : True, "res" : res}

def boothScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    # Check Product
    info = soup.find("script", type="application/ld+json", string=re.compile("Product"))
    if (info is None):
        return {"success" : False, "msg" : "Not a booth product page"}

    # Info
    info = json.loads(info.get_text())
    res = {}
    res["url"] = info["url"]
    if(info["offers"].get("price")):
        res["price"] = float(info["offers"]["price"])
    else:
        res["price"] = float(info["offers"]["highPrice"])
    res["currency"] = info["offers"]["priceCurrency"]
    butt = soup.find("button", class_="add-cart")
    if((butt is None) or ("disabled" in butt["class"])):
        res["inStock"] = False
    else:
        res["inStock"] = True

    res["origin"] = "Booth"

    return {"success" : True, "res" : res}

def bookwalkerScrape(html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("script"))

    # Check if product page
    info = soup.find("script", type = "application/ld+json")
    if(info is None):
        return {"success" : False, "msg" : "Not a bookwalker product page"}

    # Info
    info = json.loads(info.get_text())
    res = {}
    res["url"] = info["url"]
    res["price"] = float(info["offers"][0]["price"])
    res["currency"] = info["offers"][0]["priceCurrency"]
    res["inStock"] = True

    res["origin"] = "BookWalker"

    return {"success" : True, "res" : res}

def usagundamScrape(html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("meta"))

    # Check if product page
    if(soup.find("meta", property="og:type")["content"] != "product"):
        return {"success" : False, "msg" : "Not a usagundam product page"}

    # Info
    res = {}
    res["url"] = soup.find("meta", property="og:url")["content"]
    info = requestURL(res["url"] + ".oembed")["req"].json()

    res["price"] = float(info["offers"][0]["price"])
    res["currency"] = info["offers"][0]["currency_code"]
    res["inStock"] = info["offers"][0]["in_stock"]

    res["origin"] = "USA Gundam"

    return {"success" : True, "res" : res}

def surugayaScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    # Check if product page
    info = soup.find("script", type = "application/ld+json", string=re.compile("product"))
    if(info is None):
        return {"success" : False, "msg" : "Not a surugaya product page"}

    # Info
    info = info.get_text().strip()
    info = json.loads(info[1:-1])
    res = {}
    res["url"] = info["url"]
    res["price"] = float(info["offers"][0]["price"])
    res["currency"] = info["offers"][0]["priceCurrency"]
    stock = soup.find("div", class_="out-of-stock-text")
    if(stock is None):
        res["inStock"] = True
    else:
        res["inStock"] = False

    res["origin"] = "Surugaya"

    return {"success" : True, "res" : res}

SCRAPEMETHODS = {
    "aitaikuji" : requestAitaikuji
}

ORIGINS = {
    "otakurepublic" : otakuRepublicScrape,
    "goodsrepublic" : otakuRepublicScrape,
    "japanese-snacks-republic" : otakuRepublicScrape,
    "cdjapan" : cdJapanScrape,
    "aitaikuji" : aitaikujiScrape,
    "etsy" : etsyScrape,
    "omocat-shop" : omocatScrape,
    "store.crunchyroll" : crunchyrollScrape,
    "melonbooks" : melonbooksScrape,
    "goodsmileshop" : goodsmileshopScrape,
    "goodsmile" : goodsmileScrape,
    "hobby-genki" : hobbygenkiScrape,
    "solarisjapan" : solarisjapanScrape,
    "ecs.toranoana" : toranoanaScrape,
    "ec.toranoana" : toranoanaScrape,
    "hlj" : hljScrape,
    "dlsite" : dlsiteScrape,
    "booth" : boothScrape,
    "global.bookwalker" : bookwalkerScrape,
    "usagundamstore" : usagundamScrape,
    "suruga-ya" : surugayaScrape
}

def updateInfo(url):
    #Check if url is valid and if origin is part of configured sites
    origin = extractOrigin(url)
    if(origin == "N/A" or origin not in ORIGINS.keys()):
        return {"success" : False, "msg" : "Not part of configured websites"}

    try:
        if(origin in SCRAPEMETHODS.keys()):
            reqResponse = SCRAPEMETHODS[origin](url)
            info = ORIGINS[origin](reqResponse["req"])
        else:
            reqResponse = requestURL(url)

            if(not reqResponse["success"]):
                return {"success" : False}

            info = ORIGINS[origin](reqResponse["req"].text)
    except Exception as e:
        return {"success" : False, "msg" : "Something went wrong in the scrape function: " + e}

    if(info["success"]):
        return {"success" : True, "res" : info["res"], "origin" : origin}
    
    return {"success" : False, "msg" : info["msg"]}
    
async def getUpdateInfo(session, url):
    origin = extractOrigin(url)
    if(origin == "N/A" or origin not in ORIGINS.keys()):
        return {"success" : False, "msg" : "Not part of configured websites"}

    # If we can't get the loaded html with just a request
    if(origin in SCRAPEMETHODS.keys()):
        reqResponse = SCRAPEMETHODS[origin](url)
        info = ORIGINS[origin](reqResponse["req"])

        if(info["success"]):
            return {"success" : True, "res" : info["res"], "origin" : origin}
    
    # When we scrape normally
    async with session.get(url) as resp:
        if(resp.status == 404):
            return {"success" : False, "msg" : "404 Status Code"}
        
        info = ORIGINS[origin](await resp.text())

        if(info["success"]):
            return {"success" : True, "res" : info["res"], "origin" : origin}
        
        return {"success" : False, "msg" : info["msg"]}

async def scrapeInfoDatas(urlList):
    header = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    
    async with aiohttp.ClientSession(headers=header, cookies={"AUTH_ADULT" : "1"}) as session:
        tasks = []
        for url in urlList:
            tasks.append(asyncio.ensure_future(getUpdateInfo(session, url)))

        itemInfos = await asyncio.gather(*tasks)
        return itemInfos


if __name__ == "__main__":
    # pass
    # req = requestAitaikuji("https://www.aitaikuji.com/series/genshin-impact/genshin-impact-hoyoverse-official-goods-diluc-dress-shirt-black")["req"]
    # print(req)
    x = updateInfo("https://www.suruga-ya.jp/product/detail/ZHOA71527")
    # print(x["res"])
    # with open("./test.txt", "w") as f:
    #     f.write(x["res"]["img"])