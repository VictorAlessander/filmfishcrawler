from scrapy import Spider, Request, FormRequest, Selector
from scrapy.http import HtmlResponse
from re import sub
from urllib.parse import urljoin
from unidecode import unidecode
from sqlalchemy.orm import sessionmaker
from ..models import MovieShow
from ..settings import engine


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
    LOAD_MOOD_LISTS_PATH = (
        "https://www.film-fish.com/movies/index/load-mood-lists"
    )
    GET_MOVIES_FOR_PAGINATION_PATH = (
        "https://www.film-fish.com/movies/index/get-movies-for-pagination/"
    )
    SORT_MODE = "rating"

    def __init__(self, name="filmfish", **kwargs):
        self.session = self.prepare_db_session()

        super().__init__(name=name, **kwargs)

    @staticmethod
    def prepare_db_session():
        Session = sessionmaker(bind=engine)
        session = Session()
        return session.query(MovieShow)

    @staticmethod
    def sanitize_response(url, response):
        body = (
            response.text.replace("\\n", "")
            .replace('\\"', '"')
            .replace("<\\/", "</")
            .replace("\/", "/")
            .encode("utf-8")
        )
        response = HtmlResponse(url=url, body=body, encoding="utf-8")
        return Selector(response)

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
            name = element.xpath("a/text()").get().replace("\\n", "").strip()

            try:
                genre = dict(
                    id=element.xpath("a/@data-id").get().replace('\\"', ""),
                    name=name,
                )
            # Exception handling for trending genres
            except AttributeError:
                yield FormRequest(
                    url=self.MOVIES_TRENDING_PATH,
                    callback=self.parse_moods,
                    cb_kwargs=dict(
                        trending=True,
                        type_name=type_name,
                        genre_name=name,
                        referer=self.MOVIES_TRENDING_PATH,
                    ),
                    headers={"X-Requested-With": "XMLHttpRequest"},
                    formdata=dict(type=type_id),
                )
            else:
                yield FormRequest(
                    url=self.MOVIES_SUB_GENRES_PATH,
                    callback=self.parse_sub_genres,
                    cb_kwargs=dict(
                        genre_name=genre["name"]
                        .replace("\\/", "")
                        .replace('"', "")
                        .strip(),
                        type_name=type_name,
                    ),
                    headers={"X-Requested-With": "XMLHttpRequest"},
                    formdata=dict(id=genre["id"]),
                    dont_filter=True,
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
                    sub_genre_name=sub_genre["name"].replace('"', "").strip(),
                    genre_id=sub_genre["id"],
                    genre_name=genre_name,
                    type_name=type_name,
                    referer=self.MOVIES_MOOD_LIST_PATH,
                ),
                headers={"X-Requested-With": "XMLHttpRequest"},
                formdata=dict(id=sub_genre["id"]),
                dont_filter=True,
            )

    def parse_moods(
        self,
        response,
        type_name,
        genre_id=None,
        genre_name=None,
        sub_genre_name=None,
        trending=False,
        offset=0,
        referer=None,
    ):
        original_request_url = response.request.url

        response = self.sanitize_response(
            referer if referer else response.request.url, response
        )

        moods_elements = response.xpath("//div[@class='caption']")

        # Using recursion to load more content (if exists)
        if moods_elements and trending is False:
            offset += 3

            yield FormRequest(
                url=self.LOAD_MOOD_LISTS_PATH,
                callback=self.parse_moods,
                cb_kwargs=dict(
                    type_name=type_name,
                    genre_id=genre_id,
                    genre_name=genre_name,
                    sub_genre_name=sub_genre_name,
                    offset=offset,
                    referer=referer,
                ),
                headers={"X-Requested-With": "XMLHttpRequest"},
                formdata=dict(id=genre_id, offset=str(offset)),
                dont_filter=True,
            )

        for element in moods_elements:
            title = element.xpath("a/h1/i/span/text()").get()

            if title is None:
                title = element.xpath("a/h1/span/text()").get()

            mood = dict(
                title=title,
                url=element.xpath("a/@href")
                .get()
                .replace('\\"', "")
                .replace("\\n", "")
                .replace("\\", "")
                .replace("u2019", "’"),
            )

            url = urljoin(original_request_url, mood["url"])

            yield Request(
                url=url,
                cb_kwargs=dict(
                    mood_title=mood["title"],
                    type_name=type_name,
                    genre_name=genre_name,
                    sub_genre_name=sub_genre_name,
                    referer=url,
                    outside_call=True,
                ),
                callback=self.parse_movies,
                dont_filter=True,
            )

    def parse_movies(
        self,
        response,
        type_name,
        genre_name,
        sub_genre_name,
        mood_title,
        offset=0,
        mood_list_id=None,
        referer=None,
        outside_call=False,
    ):
        response = self.sanitize_response(
            referer if referer else response.request.url, response
        )

        content = response.xpath("//div[@class='header-group']")

        if offset == 0:
            mood_title = mood_title.replace("\\n", "").strip()

        if content:
            offset += 20

            if not mood_list_id:
                mood_list_variables = [
                    value.replace("=", "")
                    .replace(";", "")
                    .replace("\r", "")
                    .replace('"', "")
                    .strip()
                    for value in response.xpath("//script")[8]
                    .xpath("text()")
                    .re("=.*")
                ]
                mood_list_id = mood_list_variables[0]

            payload = (
                dict(
                    moodList=mood_list_id,
                    offset=str(offset),
                    sorting=self.SORT_MODE,
                ),
            )

            self.logger.info(f"Payload: {payload}")

            yield FormRequest(
                url=self.GET_MOVIES_FOR_PAGINATION_PATH,
                callback=self.parse_movies,
                cb_kwargs=dict(
                    type_name=type_name,
                    genre_name=genre_name,
                    sub_genre_name=sub_genre_name,
                    mood_title=mood_title,
                    offset=offset,
                    mood_list_id=mood_list_id,
                    referer=referer,
                ),
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Host": "www.film-fish.com",
                    "Origin": "https://www.film-fish.com",
                    "Referer": referer,
                },
                method="POST",
                formdata=payload[0],
                dont_filter=True,
            )

        for element in content:
            movie_title = element.xpath(
                "h4/a/span[@itemprop='name']/text()"
            ).get()

            yield self.finish(
                dict(
                    title=unidecode(movie_title.strip()),
                    type=type_name,
                    genre=genre_name,
                    sub_genre=sub_genre_name,
                    list_name=unidecode(mood_title),
                )
            )

    # TODO
    def parse_related_lists(self, response):
        related_lists_content = response.css("section.gray-section")

    def finish(self, data):
        return data
