from ast import parse
from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
import base64
import json
import requests
import re
import os
from django.conf import settings

def requestURL(url):
    header = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    try:
        req = requests.get(url, headers=header, cookies={"AUTH_ADULT" : "1"})
        if(req.status_code == 404):
            return {"success" : False, "msg" : "404 Status Code"}
    except Exception as err:
        print(f"Invalid url: {url}")
        print(err)
        return {"success" : False, "msg" : "Exception in requestURL"}
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
        return {"success" : False, "error" : "Aitaikuji request URL failed"}
    else:
        return {"success" : True, "req":html}
    finally:
        driver.quit()

IMAGE_DIR = settings.MEDIA_ROOT
rep = re.compile(r"[/\\]")
delete = re.compile(r"[#%&{}<>*?/$!'\":@+`|= ]")

# (maybeChangeInProduction)
def saveImage(name, url):
    img = requestURL(url)["req"].content
    # Sanitize the name as it might contain characters that cause problems
    temp = rep.sub("-", name)
    temp = delete.sub("", temp)
    temp = temp + ".png"
    path = os.path.join(IMAGE_DIR, temp)

    # Check if folder exists or not
    if(os.path.isdir(IMAGE_DIR) == False):
        os.makedirs(IMAGE_DIR)

    # Check if there is already a image for the product saved
    if(os.path.isfile(path) == False):
        with open(path, "wb") as f:
            f.write(img)
    return temp

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
    res["name"] = soup.find("meta", property="og:title")["content"]
    res["price"] = float(soup.find("meta", property="og:price:amount")["content"])
    res["currency"] = soup.find("meta", property="og:price:currency")["content"]
    if(soup.find("meta", property="og:availability")["content"] == "instock"):      #preorders are also listed as instock
        res["inStock"] = True
    else:
        res["inStock"] = False
    
    #requestImage
    imgURL = soup.find("meta", property="og:image")["content"].removesuffix(".l_thumbnail.webp")
    # img = base64.b64encode(requestURL(imgURL)["req"].content)
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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

    res["name"] = soup.find("meta", property="og:title")["content"].strip()
    res["price"] = float(soup.find("span", itemprop="price")["content"])
    res["currency"] = "JPY"
    if(soup.find("a", href="https://www.cdjapan.co.jp/guide/help/shipping/when_will_my_order_ship").get_text().strip() == "Sold Out"):
        res["inStock"] = False
    else:
        res["inStock"] = True
    
    #Request Image
    imgURL = soup.find("meta", property="og:image")["content"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = soup.find("meta", property="og:title")["content"]
    res["price"] = float(soup.find("meta", property="product:price:amount")["content"])
    res["currency"] = soup.find("meta", property="product:price:currency")["content"]
    if(soup.find("div", title="Availability")["class"][1] == "available"):
        res["inStock"] = True
    else:
        res["inStock"] = False

    #Request Image
    imgURL = soup.find("meta", property="og:image")["content"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = infoJSON["name"]
    if("highPrice" in infoJSON["offers"].keys()):
        res["price"] = float(infoJSON["offers"]["highPrice"])
    else:
        res["price"] = float(infoJSON["offers"]["price"])
    res["currency"] = infoJSON["offers"]["priceCurrency"]
    res["inStock"] =  (infoJSON["offers"]["availability"] == "https://schema.org/InStock")

    #Requesting Image
    if(type(infoJSON["image"]) is list):
        imgURL = infoJSON["image"][0]["contentURL"]
    else:
        imgURL = infoJSON["image"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = infoJSON["title"]
    res["price"] = float(soup.find("meta", property="og:price:amount")["content"])
    res["currency"] = soup.find("meta", property="og:price:currency")["content"]
    res["inStock"] = infoJSON["available"]

    #Request Image
    # imgURL = infoJSON["featured_image"]
    imgURL = soup.find("meta", property="og:image")["content"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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

    res["name"] = infoJSON["name"]
    res["price"] = float(infoJSON["price"])
    res["currency"] = infoJSON["currency"]
    if(soup.find("div", class_="availability")["data-available"] == "true"):
        res["inStock"] = True
    else:
        res["inStock"] = False

    #Request Image
    imgURL = "https://store.crunchyroll.com" + infoJSON["image_url"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

    res["origin"] = "Crunchyroll"

    return {"success" : True, "res" : res}

def melonbooksScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    #check if product page
    res={}
    res["url"] = soup.find("link", rel="canonical")["href"]
    if(res["url"].find("melonbooks.co.jp/detail/") < 0):
        return {"success" : False, "msg" : "Not a melonbook product page"}

    res["name"] = soup.find("h1", class_="page-header").get_text()
    res["price"] = float(soup.find("span", class_="yen").get_text().strip().removeprefix("¥"))
    res["currency"] = "JPY"
    if(soup.find("span", class_="state-instock").get_text() == "-"):
        res["inStock"] = False
    else:
        res["inStock"] = True

    #Request Image
    imgURL = soup.find("meta", property="og:image")["content"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

    res["origin"] = "Melonbooks"

    return {"success" : True, "res" : res}

def goodsmileshopScrape(html):
    soup = BeautifulSoup(html, "html.parser")

    # Check if product page
    url = soup.find("meta", property="og:url")
    if(url is None):
        return {"success" : False, "msg" : "Not a good smile product page"}

    # Info
    res = {"url" : url["content"].replace("http://ap-com.gsls", "https://goodsmileshop.com")}
    res["name"] = soup.find("div", class_="title").div.h1.get_text(strip=True)
    res["price"] = float(soup.find("div", class_="big-price").get_text(strip=True).removeprefix("¥").replace(",", ""))
    res["currency"] = "JPY"
    stock = soup.find("div", class_="qty").span
    if(stock.get_text(strip=True) == "Out of Stock"):
        res["inStock"] = False
    else:
        res["inStock"] = True

    # Request Image
    imgURL = soup.find("meta", property="og:image")["content"].replace("http://ap-com.gsls", "https://goodsmileshop.com")
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = info["name"]
    res["price"] = float(info["offers"]["price"])
    res["currency"] = info["offers"]["priceCurrency"]
    if("availability" in info["offers"]):
        res["inStock"] = True
    else:
        res["inStock"] = False

    # Request Image
    imgURL = "https://www.goodsmile.com" + info["image"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = soup.find("meta", property = "og:title")["content"]
    res["price"] = float(soup.find("meta", property = "product:price:amount")["content"])
    res["currency"] = soup.find("meta", property = "product:price:currency")["content"]
    if(soup.find("meta", property = "product:availability")["content"] == "in stock"):
        res["inStock"] = True
    else:
        res["inStock"] = False

    # Request Image
    imgURL = soup.find("meta", property="og:image")["content"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = soup.find("meta", property = "og:title")["content"]
    res["price"] = float(soup.find("meta", property = "og:price:amount")["content"].replace(",", ""))
    res["currency"] = soup.find("meta", property = "og:price:currency")["content"]
    if(res["price"] == 0):
        res["inStock"] = False
    else:
        res["inStock"] = True

    # Request Image
    imgURL = soup.find("meta", property="og:image")["content"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = info["name"].replace("\u3000", " ")
    res["price"] = float(info["offers"]["price"])
    res["currency"] = info["offers"]["priceCurrency"]
    if(info["offers"]["availability"] == "https://schema.org/SoldOut"):
        res["inStock"] = False
    else:
        res["inStock"] = True


    # Request Image
    imgURL = info["image"][0]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = info["name"]
    res["price"] = float(info["offers"]["price"])
    res["currency"] = info["offers"]["priceCurrency"]
    if((info["offers"]["availability"] == "https://schema.org/InStock") or (info["offers"]["availability"] == "https://schema.org/PreOrder")):
        res["inStock"] = True
    else:
        res["inStock"] = False

    # Request Image
    imgURL = info["image"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = info["data-work_name"]
    res["price"] = float(info["data-price"])
    res["currency"] = "JPY"
    res["inStock"] = True                   #Digital item so always true

    # Request an Image
    imgURL = soup.find("meta", property="og:image")["content"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = info["name"]
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

    # Request Image
    imgURL = info["image"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = info["name"]
    res["price"] = float(info["offers"][0]["price"])
    res["currency"] = info["offers"][0]["priceCurrency"]
    res["inStock"] = True
    # res["image"] = info["image"]
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("img"))
    imgURL = soup.find("img", itemprop="image")["src"]
    res["img"] = saveImage(res["name"], imgURL)

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

    res["name"] = info["title"]
    res["price"] = float(info["offers"][0]["price"])
    res["currency"] = info["offers"][0]["currency_code"]
    res["inStock"] = info["offers"][0]["in_stock"]

    # Request Image
    imgURL = soup.find("meta", property="og:image:secure_url")["content"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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
    res["name"] = info["name"]
    res["price"] = float(info["offers"][0]["price"])
    res["currency"] = info["offers"][0]["priceCurrency"]
    stock = soup.find("div", class_="out-of-stock-text")
    if(stock is None):
        res["inStock"] = True
    else:
        res["inStock"] = False

    # Request image
    imgURL = info["image"]
    # img = "data:image/jpeg;base64," + base64.b64encode(requestURL(imgURL)["req"].content).decode("utf-8")
    res["img"] = saveImage(res["name"], imgURL)

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

def scrapeInfo(url):
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
                return {"success" : False, "msg" : "Request URL failed"}

            info = ORIGINS[origin](reqResponse["req"].text)
    except Exception as e:
        return {"success" : False, "msg" : "Something went wrong in the scrape function: " + e}

    if(info["success"]):
        return {"success" : True, "res" : info["res"]}
    
    return {"success" : False, "msg" : info["msg"]}
    


if __name__ == "__main__":
    pass
    # req = requestURL("https://www.etsy.com/listing/1230404476/hololive-vtuber-hoshimachi-suisei-enamel?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=suisei&ref=sr_gallery-1-1&sts=1&organic_search_click=1&variation0=2648039902")["req"]
    # print(req.text)
    # x = scrapeInfo("https://www.suruga-ya.jp/product/detail/ZHOA71527")
    # print(x)
    # print(x["res"])
    # with open("./test.txt", "w") as f:
    #     f.write(x["res"]["img"])
    # saveImage("test test.png", "https://otakurepublic.com/media/binary/003/066/832/3066832.jpg")