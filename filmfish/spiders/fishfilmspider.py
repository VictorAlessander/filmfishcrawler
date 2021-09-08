from scrapy import Spider, Request, FormRequest
from re import sub


class FilmFishSpider(Spider):
    name = "filmfish"
    start_urls = ["https://www.film-fish.com/"]
    TYPE_GENRES_PATH = (
        "https://www.film-fish.com/movies/index/get-genres-by-type"
    )
    MOOD_LIST_PATH = "https://www.film-fish.com/movies/index/get-mood-lists"
    SUB_GENRES_PATH = "https://www.film-fish.com/movies/index/get-sub-genre"

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_types, dont_filter=True)

    def parse_types(self, response):
        movies_type = response.css("a#homeMoviesNav")
        tvshow_type = response.css("a#homeTvNav")

        types = [
            movies_type.xpath("@data-type").get(),
            tvshow_type.xpath("@data-type").get(),
        ]

        for type_id in types:
            yield FormRequest(
                url=self.TYPE_GENRES_PATH,
                callback=self.parse_genres,
                headers={"X-Requested-With": "XMLHttpRequest"},
                formdata=dict(type=type_id),
            )

    def parse_genres(self, response):
        genres_ids = sorted(
            [
                element.get().replace('\\"', "")
                for element in response.xpath("//a/@data-id")
            ]
        )

        for genre_id in genres_ids:
            yield FormRequest(
                url=self.SUB_GENRES_PATH,
                callback=self.parse_sub_genres,
                headers={"X-Requested-With": "XMLHttpRequest"},
                formdata=dict(id=genre_id),
            )

    def parse_sub_genres(self, response):
        sub_genres_ids = sorted(
            [
                sub('[\\\\n"]', "", element.get())
                for element in response.xpath("//a/@data-id")
            ]
        )

        for sub_genre_id in sub_genres_ids:
            yield FormRequest(
                url=self.MOOD_LIST_PATH,
                callback=self.parse_moods,
                headers={"X-Requested-With": "XMLHttpRequest"},
                formdata=dict(id=sub_genre_id),
            )

    def parse_moods(self, response):
        moods_urls = [
            element.get()
            for element in response.xpath(
                "//div[@class='{}']/a/@href".format('\\"footer-group\\"')
            )
        ]

        for mood_url in moods_urls:
            yield Request(
                url=response.request.urljoin(mood_url),
                callback=self.parse_movies,
            )

    def parse_movies(self, response):
        pass
