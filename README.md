# Wish List Project[^1]
A web application that allows users to add items/products using a url of a shopping website that has been configured. The website keeps the compilation of items and allows users to see and organize what they want to buy in one place.

This is a thread of short videos on how the site work. [Link](https://x.com/AstralCzzz/status/1770337003181076607?s=20)

## Commands
```
   myworld/Scripts/activate
   cd .\wishlist\
   py manage.py runserver
   cd ..
   deactivate
```


## List of configured sites
A list of sites that has been configured to scrape info of items from. [^2]
1. Republic
    * Otaku Republic
    * Goods Republic
    * Japanese-snacks-republic
    * Figure Republic 
2. CDJapan
3. Aitaikuji
4. Etsy
5. Omocat
6. Crunchyroll
7. Melonbooks
8. GoodSmile
    * Good Smile Shop
    * Good Smile
9. Hobby Genki
10. Solaris Japan
11. Toranoana
12. HobbyLink Japan
13. DLSite
14. Booth
15. BookWalker
    * Global
    * jp
16. USA Gundam
17. Surugaya


## List of Packages used
  * Scraping
    * Beautiful Soup
    * requests
    * selenium
      * Uses gecko driver
    * re
    * json
    * Asynchronous Scraping
      * aiohttp
      * asyncio
  * Website
    * Django


[^1]: Has not been configured for production. If sent to production some things might need to change such as how images are handled.
[^2]: I don't use half of these sites so I probably won't notice if a scrape doesn't work because the website has updated or changed after time passes.
