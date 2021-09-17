from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String


DeclarativeBase = declarative_base()


def create_table(engine):
    DeclarativeBase.metadata.create_all(engine)


class MovieShow(DeclarativeBase):
    __tablename__ = "movieshow"

    id = Column("id", Integer, primary_key=True)
    title = Column("title", String)
    type = Column("type", String)
    genre = Column("genre", String)
    sub_genre = Column("sub_genre", String)
    list_name = Column("list_name", String)
