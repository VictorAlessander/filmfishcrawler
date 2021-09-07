from scrapy import Spider


class FishFilmSpider(Spider):
    name = "fishfilm"
    start_urls = []

    def parse(self, response, **kwargs):
        pass
