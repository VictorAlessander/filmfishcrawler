from scrapy import Item, Field


class MovieItem(Item):
    title = Field()
    type = Field()
    genre = Field()
    sub_genre = Field()
    list_name = Field()
