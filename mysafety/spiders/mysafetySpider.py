import json
import scrapy
from w3lib.http import basic_auth_header
from mysafety.items import ScrapedProduct, ScrapedCategory, ScrapedProductCategoryAssociation
from mysafety.countrysettings import countries
from hashlib import sha1
import re
import requests


class mysafetySpider(scrapy.Spider):
    name = "mysafetyspider"

    def start_requests(self):
        return [scrapy.Request(
            url=x['url'],
            callback=self.parsemainpage,
            cb_kwargs={
                "countryinfo": x,
            }
        ) for x in countries]

    def parsemainpage(self, response: scrapy.http.Response, countryinfo: dict):
        maincats = response.xpath('//ul[@class="menu"]/li')[0].xpath('ul/li')

        for mainitem in maincats:
            maincat = ScrapedCategory()
            maincat['name'] = mainitem.xpath('a/text()').get()
            maincat['url'] = response.urljoin(mainitem.xpath('a/@href').get())
            maincat['level'] = 1
            maincat['platformcategoryid'] = self.generateidfromurl(maincat['url'])
            maincat['agegroup'] = "adult"
            maincat['targetgender'] = "unisex"
            maincat['storeid'] = countryinfo['storeid']

            # yield maincat

            yield scrapy.Request(
                url=maincat['url'],
                callback=self.parseprodpage,
                cb_kwargs={
                    "countryinfo": countryinfo,
                    "category": maincat
                }
            )

    def parseprodpage(self, response: scrapy.http.Response, category: ScrapedCategory, countryinfo: dict):
        category['generatedkeywords'] = response.xpath(
            '//div[@class="usp"]/div[@class="usp__content"]/h3/text()').getall()
        yield category
        newprod = ScrapedProduct()
        newprod['name'] = response.xpath('//div[@class="buy-now__title"]/h2/div/text()').get().strip("\n").strip()
        newprod['name'] = category['name']
        newprod['url'] = response.url
        newprod['price'] = response.xpath('//span[@class="product__price"]/text()').get()
        newprod['saleprice'] = None
        newprod['platformproductid'] = self.generateidfromurl(newprod['url'])
        newprod['platformcategoryid'] = category['platformcategoryid']
        newprod['additionalcategoryids'] = []
        newprod['gender'] = "unisex"
        newprod['agegroup'] = "adult"
        newprod['storeid'] = countryinfo['storeid']
        cleanr = re.compile("<.*?>")
        rawdesclist = response.xpath('//div[@class="field-shared-header-text"]').getall()
        newprod['description'] = re.sub(cleanr, ' ', " ".join(rawdesclist)).strip().replace(
            "\n", ".").replace(" .", ".")
        newprod['imageLink'] = response.xpath('//div[@class="product-info-wrapper__image"]/@data-src').get()
        newprod['additionalImageLinks'] = []
        newprod['gender'] = "unisex"
        newprod['material'] = ""
        newprod['color'] = ""
        newprod['shipping'] = ""
        newprod['shippingWeight'] = ""
        newprod['sizes'] = [None]
        newprod['gtin'] = [None]
        newprod['mpn'] = None
        newprod['brand'] = response.xpath('//div[@class="header__logo"]/a/img/@title').get()
        newprod['platformvariantid'] = "1"

        yield newprod


        # newprod['']

    @staticmethod
    def generateidfromurl(url: str) -> str:
        sha = sha1()
        sha.update(url.encode("utf-8"))
        return sha.hexdigest()[-15:]
