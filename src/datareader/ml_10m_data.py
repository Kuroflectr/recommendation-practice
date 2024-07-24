from datetime import datetime
from datareader.db import fetch_datas, get_tables
from pydantic import BaseModel
from datareader.ml_data_base import AbstractDatas
from table_models.ml_10m.settings import Movies as Movies_model
from table_models.ml_10m.settings import Tags as Tags_model
from core.config import settings
from enum import Enum


# Define the Enum for the label
class Label(str, Enum):
    train = "train"
    test = "test"


class Rating(BaseModel):
    user_id: int
    movie_id: int
    rating: int
    timestamp: datetime
    label: Label


class Movie(BaseModel):
    movie_id: int
    title: str
    genres: list[str]


class Tag(BaseModel):
    id: int
    user_id: int
    movie_id: int
    tag: str
    timestamp: datetime


class IntegratedData(BaseModel):
    user_id: int
    movie_id: int
    rating: int
    movie_title: str
    movie_year: int
    genres: list[str]
    timestamp: datetime
    label: Label


class PopularityTrainData(BaseModel):
    movie_id: int
    title: str
    ave_rating: float
    rated_movies_count: int


class PopularityTestData(BaseModel):
    user_id: int
    movie_id: int
    title: str
    rating: int


class Ratings(AbstractDatas):
    data: list[Rating]

    @classmethod
    async def from_db(cls, user_num=1000) -> "Ratings":
        with open(settings.sql_dir / "ratings.sql", "r") as f:
            sql_query = f.read()

        args = {"user_num": user_num}
        ratings = await get_tables(sql_query=sql_query, args=args)
        read_data = [
            Rating(
                user_id=rating.user_id,
                movie_id=rating.movie_id,
                rating=rating.rating,
                timestamp=rating.timestamp,
                label=rating.label,
            )
            for rating in ratings
        ]
        return cls(data=read_data)


class Movies(AbstractDatas):
    data: list[Movie]

    @classmethod
    async def from_db(cls) -> "Movies":
        movies = await fetch_datas(Movies_model)
        read_data = [
            Movie(
                movie_id=movie.movie_id,
                title=movie.title,
                genres=movie.genres.split("|"),
            )
            for movie in movies
        ]
        return cls(data=read_data)


class Tags(AbstractDatas):
    data: list[Tag]

    @classmethod
    async def from_db(cls) -> "Tags":
        tags = await fetch_datas(Tags_model)
        # Read the tag in lower case
        read_data = [
            Tag(
                id=tag.id,
                user_id=tag.user_id,
                movie_id=tag.movie_id,
                tag=tag.tag.lower(),
                timestamp=tag.timestamp,
            )
            for tag in tags
        ]
        return cls(data=read_data)


class IntegratedDatas(AbstractDatas):
    data: list[IntegratedData]

    @classmethod
    async def from_db(cls, user_num=1000) -> "IntegratedDatas":
        with open(settings.sql_dir / "integrated_tables.sql", "r") as f:
            sql_query = f.read()

        args = {"user_num": user_num}
        integrated_datas = await get_tables(sql_query=sql_query, args=args)
        read_data = [
            IntegratedData(
                user_id=row.user_id,
                movie_id=row.movie_id,
                rating=row.rating,
                movie_title=row.movie_title,
                movie_year=row.movie_year,
                genres=row.genres.split("|"),
                timestamp=row.timestamp,
                label=row.label,
            )
            for row in integrated_datas
        ]
        return cls(data=read_data)


class PopularityDatas(BaseModel):
    train_data: list[PopularityTrainData]
    test_data: list[PopularityTestData]

    @classmethod
    async def from_db(cls, user_num=1000, threshold=50) -> "PopularityDatas":
        # Read the training data
        with open(settings.sql_dir / "popularityrecommender_train.sql", "r") as f:
            sql_query = f.read()

        args = {"user_num": user_num, "threshold": threshold}
        popularity_train_datas = await get_tables(sql_query=sql_query, args=args)
        read_train_data = [
            PopularityTrainData(
                movie_id=row.movie_id,
                title=row.title,
                ave_rating=row.ave_rating,
                rated_movies_count=row.rated_movies_count,
            )
            for row in popularity_train_datas
        ]

        # Read the test data
        with open(settings.sql_dir / "popularityrecommender_test.sql", "r") as f:
            sql_query = f.read()

        args = {"user_num": user_num}
        popularity_test_datas = await get_tables(sql_query=sql_query, args=args)
        read_test_data = [
            PopularityTestData(
                user_id=row.user_id,
                movie_id=row.movie_id,
                title=row.title,
                rating=row.rating,
            )
            for row in popularity_test_datas
        ]

        return cls(train_data=read_train_data, test_data=read_test_data)

    def split_data(self):
        return (self.train_data, self.test_data)


if __name__ == "__main__":
    import asyncio
    import time

    # async def _main():
    #     ratings = await Ratings.from_db()
    #     train_data, test_data = ratings.split_data()
    #     print(test_data[0])
    #     print(test_data[1])
    #     print(len(ratings.data))
    #     print(len(test_data))
    #     print(len(train_data))

    # async def _main():
    #     movies = await Movies.from_db()
    #     train_data, test_data = movies.split_data()
    #     print(movies.data[0])

    #     print(test_data[0])
    #     print(test_data[1])
    #     print("length of all data: ", len(movies.data))
    #     print(len(test_data))
    #     print(len(train_data))

    # async def _main():
    #     movies = await PopularityTrainDatas.from_db()
    #     print(movies.data[0])
    #     train_data, test_data = movies.split_data()
    #     print(test_data[0])
    #     print(test_data[1])
    #     print("length of all data: ", len(movies.data))
    #     print("length of test data: ", len(test_data))
    #     print("length of train data: ", len(train_data))

    async def _main():
        movies = await PopularityDatas.from_db(user_num=1000, threshold=30)
        train_data, test_data = movies.split_data()
        print(test_data[0])
        print(test_data[1])
        # print("length of all data: ", len(movies.data))
        print("length of test data: ", len(test_data))
        print("length of train data: ", len(train_data))

    print("loading movie lense data")
    start_time = time.time()
    asyncio.run(_main())
    end_time = time.time()
    print("time lapsed: ", end_time - start_time)
