from scrapy import Spider, Request, FormRequest
from re import sub
from urllib.parse import urljoin


class FilmFishSpider(Spider):
    name = "filmfish"
    start_urls = ["https://www.film-fish.com/"]
    MOVIES_TYPE_GENRES_PATH = (
        "https://www.film-fish.com/movies/index/get-genres-by-type"
    )
    MOVIES_MOOD_LIST_PATH = (
        "https://www.film-fish.com/movies/index/get-mood-lists"
    )
    MOVIES_SUB_GENRES_PATH = (
        "https://www.film-fish.com/movies/index/get-sub-genre"
    )
    MOVIES_TRENDING_PATH = (
        "https://www.film-fish.com/movies/index/get-trending-mood-lists"
    )

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_types, dont_filter=True)

    def parse_types(self, response):
        movies_type = response.css("a#homeMoviesNav")
        tvshow_type = response.css("a#homeTvNav")

        types = [
            dict(
                id=movies_type.xpath("@data-type").get(),
                name=movies_type.css("::text").get().strip(),
            ),
            dict(
                id=tvshow_type.xpath("@data-type").get(),
                name=tvshow_type.css("::text").get().strip(),
            ),
        ]

        for type in types:
            yield FormRequest(
                url=self.MOVIES_TYPE_GENRES_PATH,
                callback=self.parse_genres,
                cb_kwargs=dict(type_id=type["id"], type_name=type["name"]),
                headers={"X-Requested-With": "XMLHttpRequest"},
                formdata=dict(type=type["id"]),
            )

    def parse_genres(self, response, type_id, type_name):
        genres_elements = response.css("div")

        for element in genres_elements:
            try:
                genre = dict(
                    id=element.xpath("a/@data-id").get().replace('\\"', ""),
                    name=element.xpath("a/text()")
                    .get()
                    .replace("\\n", "")
                    .strip(),
                )
            except AttributeError:
                yield FormRequest(
                    url=self.MOVIES_TRENDING_PATH,
                    callback=self.parse_moods,
                    cb_kwargs=dict(trending=True, type_name=type_name),
                    headers={"X-Requested-With": "XMLHttpRequest"},
                    formdata=dict(type=type_id),
                )
            else:
                yield FormRequest(
                    url=self.MOVIES_SUB_GENRES_PATH,
                    callback=self.parse_sub_genres,
                    cb_kwargs=dict(
                        genre_name=genre["name"], type_name=type_name
                    ),
                    headers={"X-Requested-With": "XMLHttpRequest"},
                    formdata=dict(id=genre["id"]),
                )

    def parse_sub_genres(self, response, type_name, genre_name):
        sub_genres_elements = response.xpath("//div")

        for element in sub_genres_elements:
            sub_genre = dict(
                id=sub('[\\\\n"]', "", element.xpath("a/@data-id").get()),
                name=element.xpath("a/text()")
                .get()
                .replace("\\n", "")
                .strip(),
            )

            yield FormRequest(
                url=self.MOVIES_MOOD_LIST_PATH,
                callback=self.parse_moods,
                cb_kwargs=dict(
                    sub_genre_name=sub_genre["name"],
                    genre_name=genre_name,
                    type_name=type_name,
                ),
                headers={"X-Requested-With": "XMLHttpRequest"},
                formdata=dict(id=sub_genre["id"]),
            )

    def parse_moods(
        self,
        response,
        type_name,
        genre_name=None,
        sub_genre_name=None,
        trending=False,
    ):
        moods_elements = response.xpath(
            "//div[@class='{}']".format('\\"caption\\"')
        )

        for element in moods_elements:
            mood = dict(
                title=element.xpath("a/h1/i/span/text()").get()
                if trending
                else element.xpath("a/h1/span/text()").get(),
                url=element.xpath("a/@href")
                .get()
                .replace('\\"', "")
                .replace("\\n", "")
                .replace("\\", ""),
            )

            yield Request(
                url=urljoin(response.request.url, mood["url"]),
                cb_kwargs=dict(
                    mood_title=mood["title"],
                    type_name=type_name,
                    genre_name=genre_name,
                    sub_genre_name=sub_genre_name,
                ),
                callback=self.parse_movies,
            )

    def parse_movies(
        self, response, type_name, genre_name, sub_genre_name, mood_title
    ):
        content = response.xpath(
            "//li[@itemprop='itemListElement']/div[@class='row']/div/div/div/div[@class='right-wrp']"
        )

        for element in content:
            movie_title = element.xpath(
                "div[@class='header-group']/h4/a/span[@itemprop='name']/text()"
            ).get()

            return dict(
                title=movie_title.strip(),
                type=type_name,
                genre=genre_name.replace('"', "").strip(),
                sub_genre=sub_genre_name,
                list_name=mood_title.replace("\\n", "").strip(),
            )
