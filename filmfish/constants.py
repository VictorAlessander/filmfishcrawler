MOVIES_TYPE_GENRES_PATH = (
    "https://www.film-fish.com/movies/index/get-genres-by-type"
)
MOVIES_MOOD_LIST_PATH = "https://www.film-fish.com/movies/index/get-mood-lists"
MOVIES_SUB_GENRES_PATH = "https://www.film-fish.com/movies/index/get-sub-genre"
MOVIES_TRENDING_PATH = (
    "https://www.film-fish.com/movies/index/get-trending-mood-lists"
)
LOAD_MOOD_LISTS_PATH = "https://www.film-fish.com/movies/index/load-mood-lists"
GET_MOVIES_FOR_PAGINATION_PATH = (
    "https://www.film-fish.com/movies/index/get-movies-for-pagination/"
)
SORT_MODE = "rating"


def get_movies_for_pagination_headers(referer):
    return {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Host": "www.film-fish.com",
        "Origin": "https://www.film-fish.com",
        "Referer": referer,
    }
