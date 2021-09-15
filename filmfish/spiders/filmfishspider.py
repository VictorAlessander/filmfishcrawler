from scrapy import Spider, Request, FormRequest
from re import sub
from urllib.parse import urljoin
from unidecode import unidecode


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
            except AttributeError:
                yield FormRequest(
                    url=self.MOVIES_TRENDING_PATH,
                    callback=self.parse_moods,
                    cb_kwargs=dict(
                        trending=True, type_name=type_name, genre_name=name
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
    ):
        moods_elements = response.xpath(
            "//div[@class='{}']".format('\\"caption\\"')
        )

        # Using recursion to load more content (if exists)
        if moods_elements and trending is False:
            offset += 3

            try:
                yield FormRequest(
                    url=self.LOAD_MOOD_LISTS_PATH,
                    callback=self.parse_moods,
                    cb_kwargs=dict(
                        type_name=type_name,
                        genre_id=genre_id,
                        genre_name=genre_name,
                        sub_genre_name=sub_genre_name,
                        offset=offset,
                    ),
                    headers={"X-Requested-With": "XMLHttpRequest"},
                    formdata=dict(id=genre_id, offset=str(offset)),
                    dont_filter=True,
                )
            # Probably nothing was returned from form request
            except TypeError:
                self.logger.info(
                    f"[-] Found a possible endline in {type_name} > {genre_name} > {sub_genre_name}."
                )
                pass

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
    ):
        content = response.xpath(
            "//li[@itemprop='itemListElement']/div[@class='row']/div/div/div/div[@class='right-wrp']"
        )

        if not content:
            content = response.xpath(
                "//li[@itemprop='{}']//div[@class='{}']".format(
                    '\\"itemListElement\\"', '\\"right-wrp\\"'
                )
            )

        if offset == 0:
            mood_title = mood_title.replace("\\n", "").strip()

        if content:
            offset += 5

            try:
                if not mood_list_id:
                    get_payload = [
                        value.replace("=", "")
                        .replace(";", "")
                        .replace("\r", "")
                        .replace('"', "")
                        .strip()
                        for value in response.xpath("//script")[8]
                        .xpath("text()")
                        .re("=.*")
                    ]

                yield FormRequest(
                    url=self.GET_MOVIES_FOR_PAGINATION_PATH,
                    callback=self.parse_movies,
                    cb_kwargs=dict(
                        type_name=type_name,
                        genre_name=genre_name,
                        sub_genre_name=sub_genre_name,
                        mood_title=mood_title,
                        offset=offset,
                        mood_list_id=mood_list_id
                        if mood_list_id
                        else get_payload[0],
                    ),
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "Accept-Encoding": "gzip, deflate, br",
                    },
                    formdata=dict(
                        moodList=mood_list_id
                        if mood_list_id
                        else get_payload[0],
                        offset=str(offset),
                        sort=self.SORT_MODE,
                    ),
                    dont_filter=True,
                )
            # Probably nothing was returned from form request
            except TypeError as exc:
                self.logger.info(
                    f"[-] Found a possible endline in mood: {mood_title}."
                )
                pass

        for element in content:

            movie_title = element.xpath(
                "div[@class='header-group']/h4/a/span[@itemprop='name']/text()"
            ).get()

            if not movie_title:
                movie_title = element.xpath(
                    "div[@class='{}']/h4/a/span[@itemprop='{}']/text()".format(
                        '\\"header-group\\"', '\\"name\\"'
                    )
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

    def parse_related_lists(self, response):
        related_lists_content = response.css("section.gray-section")

    def finish(self, data):
        return data
