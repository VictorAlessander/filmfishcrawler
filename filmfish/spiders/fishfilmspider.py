from scrapy import Spider


class FishFilmSpider(Spider):
    name = "fishfilm"
    start_urls = ["https://www.film-fish.com/"]

    def parse(self, response, **kwargs):
        pass
