# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from sqlalchemy.orm import sessionmaker
from .models import MovieShow
from .settings import engine
from scrapy.exceptions import DropItem


class FilmFishPipeline:
    def __init__(self) -> None:
        self.session = self.prepare_db_session()

    @staticmethod
    def prepare_db_session():
        Session = sessionmaker(bind=engine)
        return Session()

    def process_item(self, item, spider):
        item_adapter = ItemAdapter(item)

        item_exists = (
            self.session.query(MovieShow)
            .filter_by(
                title=item_adapter["title"],
                genre=item_adapter["genre"],
                sub_genre=item_adapter["sub_genre"],
                list_name=item_adapter["list_name"],
            )
            .first()
        )

        if item_exists:
            raise DropItem(f"Duplicated item found: {item_adapter!r}")

        new_movieshow = MovieShow(**item_adapter)
        self.session.add(new_movieshow)
        self.session.commit()

        return item
