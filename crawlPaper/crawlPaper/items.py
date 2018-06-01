# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy, json


class CrawlpaperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name  = scrapy.Field()
    citeUrl = scrapy.Field()
    url   = scrapy.Field()
    downloadUrl = scrapy.Field()
    local = scrapy.Field()
    dir = scrapy.Field()
    subject = scrapy.Field()

    time  = scrapy.Field()
    cite  = scrapy.Field()
    cited = scrapy.Field()

def citationParse():
    paperItem = CrawlpaperItem()
    paperItem["name"] = 'asdasdada'
    paperItem["citeUrl"] = "zcawejmoqlnslad"
    paperItem["url"] = "asdnsdoiq"
    paperItem["downloadUrl"] = "sdwefwvrdv"
    paperItem["dir"] = 'szdsdsfcscs'
    paperItem["local"] = "sqeq2wdewfdl,klm"

    with open('../papers/citationsMes.txt', 'a+',encoding='utf-8') as f:
        jsontext=json.dumps(dict(paperItem),ensure_ascii=False) + ",\n"
        f.write(jsontext)

# citationParse()
