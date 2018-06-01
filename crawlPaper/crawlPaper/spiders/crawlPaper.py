import scrapy
import re
from scrapy.spiders import CrawlSpider
from httplib2 import Response, has_timeout
from crawlPaper.items import CrawlpaperItem
import os, json
from mylib.texthelper.myprint import MPrint

class PaperMes():
    def __init__(self, name, cited_url, download_url):
        self.name = name
        self.cited_url = cited_url
        self.download_url = download_url

def itemTojson(item):
    jsontext=json.dumps(dict(item),ensure_ascii=False) + ",\n"
    return jsontext

class PaperSpider(CrawlSpider):
    name = 'crawlPaper'
    start_urls = []
    global paperList
    paperList = [
                    "Attention is all you need" \
                ]
    for paper in paperList:
        start_urls.append("https://scholar.google.co.jp/scholar?hl=en&as_sdt=0%2C5&q={0}&btnG=".format('+'.join(paper.split(' '))))

    def __init__(self):
        global paperList
        self.root = "https://scholar.google.co.jp"
        self.paperList = paperList
        self.mprint = MPrint("./logging.txt")
        self.paperItems = []
        self.citations = []
        self.paperItem = CrawlpaperItem()
        self.paperItem["cited"] = []
        self.dir = "./papers/"
    def parse(self, response):
        self.paperItems = self.scholarParse(response)
        self.citations = self.scholarParse(response)
        self.mprint.plist2f(self.paperItems,"paperItem")
        for paperItem in self.paperItems:
            if paperItem["name"] in self.paperList:
                self.paperItem = paperItem
                if not os.path.exists(paperItem["dir"]):
                    os.makedirs(paperItem["dir"])
                if not os.path.exists(paperItem["local"]):
                    excution = "wget {0} -O {1}".format(paperItem["downloadUrl"],paperItem["local"])
                    os.system(excution)
                if not os.path.exists(paperItem["dir"]+'/paperMes.txt'):
                    mprintP =MPrint(paperItem["dir"]+'/paperMes.txt')
                    mprintP.pstr2f(paperItem, "paperItem")
                overUrl = self.overCiteUrl(paperItem["citeUrl"])
                yield scrapy.FormRequest(overUrl,callback = self.maxCiteParse)


    def maxCiteParse(self,response):
        self.mprint.pstr2f(response.url, "response.url")
        maxIndex = response.xpath("//td/a/text()").extract()
        if maxIndex != []:
            maxIndex = response.xpath("//td/a/text()").extract()[-1]
            for i in range(int(maxIndex)):
                maxUrl = re.sub('100000',str(i)+'0',response.url)
                yield scrapy.FormRequest(maxUrl,callback = self.citationParse)
        else:
            maxUrl = re.sub('100000','00',response.url)
            # yield scrapy.FormRequest(maxUrl,callback = self.overCiteUrl)

    def citationParse(self, response):
        citations = self.scholarParse(response)
        for citation in citations:
            with open(self.paperItem["dir"]+'/citationsMes.txt', 'a+',encoding='utf-8') as f:
                jsontext=json.dumps(dict(paperItem),ensure_ascii=False) + ",\n"
                f.write(jsontext)

    def overCiteUrl(self, rawUrl):
        root = "https://scholar.google.co.jp/scholar?cites="
        citehash = re.search('cites=\d*',self.root+rawUrl).group()[6:]
        otherIndex = (self.root+rawUrl)[len(citehash+root):].split('&')
        pre_root = root[:-6]+"start="
        aff_root = "&{0}".format(otherIndex[-1])+"&{0}".format(otherIndex[-3])+"&cites="+ "{0}".format(citehash)+"&scipsc=1"
        overCiteUrl = pre_root+ "{0}".format('100000')+aff_root
        return overCiteUrl
        # print(overCiteUrl, end="\n" ,file=self.logging)

    def scholarParse(self, response):
        # paper是该页面中除去有标注为citation之外的论文名称列表
        papers_mes = response.xpath("//div[@class='gs_ri']/h3[@class='gs_rt']/a").extract()
        papers_withb = [re.search('">.*</a',text).group()[2:-3] for text in papers_mes]
        papers = [re.sub('</?b>','',text).rstrip('.') for text in papers_withb]
        papers_url = response.xpath("//div[@class='gs_ri']/h3[@class='gs_rt']/a/@href").extract()
        self.mprint.plist2f(papers, name="papers")
        self.mprint.plist2f(papers_url, name="papers_url")

        # Cited_url 由于有的论文是没有被引用的, 这样每个论文的条目结构是不同的.有1的代表这个subscription下是有cited by的, 0是代表没有.
        citations = []
        subscriptions = response.xpath("//div[@class='gs_ri']/h3[@class='gs_rt']/a/../following-sibling::div[@class='gs_fl']").extract()
        Cited_url = response.xpath("//div[@class='gs_ri']/h3[@class='gs_rt']/a/../following-sibling::div[@class='gs_fl']/a[contains(text(),'Cited by')]/@href").extract()
        i = 0
        for subscription in subscriptions:
            if "Cited by" in subscription:
                citations.append(Cited_url[i])
                i += 1
            else:
                citations.append(None)
        # self.mprint.plist2f(citations, name="citations")

        # 由于有的论文是没有论文地址的, 这样每个论文的条目结构是不同的.有1的代表这一片文章有
        download_urls = []
        all_div = response.xpath("//div[@class='gs_ri']/h3[@class='gs_rt']/a/../../../../div[@class='gs_r gs_or gs_scl']/div").extract()
        pdf_url = response.xpath("//div[@class='gs_ri']/h3[@class='gs_rt']/a/../../../div[@class='gs_ggs gs_fl']/div/div/a/@href").extract()
        i = 0
        j = 0
        while(i<len(all_div)):
            if "[CITATION]" in all_div[i]:
                if "gs_ggs gs_fl" in all_div[i]:
                    i += 1
                i += 1
            else:
                if "gs_ggs gs_fl" in all_div[i]:
                    download_urls.append(pdf_url[j])
                    i += 2
                    j += 1
                else:
                    download_urls.append(None)
                    i += 1
        self.mprint.plist2f(download_urls, name="download_urls")
        self.mprint.plist2f(paperList, name="paperList")

        paperItems = []
        for i in range(len(papers)):
            paperItem = CrawlpaperItem()
            paperItem["name"] = papers[i]
            paperItem["citeUrl"] = citations[i]
            paperItem["url"] = papers_url[i]
            paperItem["downloadUrl"] = download_urls[i]
            paperItem["dir"] = self.dir + '_'.join(papers[i].split())
            paperItem["local"] = paperItem["dir"] + '/'+'_'.join(papers[i].split())+'.pdf'
            paperItems.append(paperItem)
        # mprint.plist2f(paperItems, name="paperItems")
        return paperItems

if __name__ == "__main__":
    pass
