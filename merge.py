from dataclasses import dataclass, field
from typing import Optional, Self
import json
import random
from datetime import datetime

import psycopg2 as pg

@dataclass
class TourMetadata:
    max_adults: Optional[int] = None
    max_kids: Optional[int] = None
    transport_type: list[str] = field(default_factory=lambda: [])
    room_type: list[str] = field(default_factory=lambda: [])

@dataclass
class Tour:
    operator: str
    hotel: str
    country: str
    city: str
    score: float
    description: str
    thumbnail_url: str

    metadata: TourMetadata

    def insert_into_db(self, cursor, table_name: str = "Tour"):
        # CREATE TABLE Tour (
        #     id bigserial primary key,
        #     operator varchar(128) not null,
        #     hotel varchar(128) not null,
        #     country varchar(128) not null,
        #     city varchar(256) not null,
        #     description text,
        #     thumbnail_url varchar(256) not null
        #     score smallint not null,
        # );
        cursor.execute(f"INSERT INTO {table_name} (operator, hotel, country, city, description, thumbnail_url, score) VALUES %s RETURNING id",
                       ((self.operator,
                        self.hotel,
                        self.country,
                        self.city,
                        self.description,
                        self.thumbnail_url,
                        self.score),))
        return cursor.fetchone()[0]


@dataclass
class Offer:
    arrival_date: datetime
    departure_date: datetime
    transport: str
    number_of_adults: int
    number_of_kids: int
    room_type: str

    def insert_into_db(self, cursor, tour_id: int, table_name: str = "Offer"):
        # CREATE TABLE Offer (
        #     id bigserial primary key,
        #     tour_id bigserial references Tour (id),
        #     arrival_date date not null,
        #     departure_date date not null,
        #     transport varchar(128) not null,
        #     number_of_kids smallint not null,
        #     number_of_adults smallint not null,
        #     room_type varchar(128) not null,
        #     available boolean not null default true,
        # );
        cursor.execute(f"INSERT INTO {table_name} (tour_id, arrival_date, departure_date, transport, number_of_kids, number_of_adults, room_type, available) VALUES %s RETURNING id",
                       ((tour_id,
                         self.arrival_date,
                         self.departure_date,
                         self.transport,
                         self.number_of_kids,
                         self.number_of_adults,
                         self.room_type,
                         True),))
        return cursor.fetchone()[0]

    @staticmethod
    def random_from_tour(tour: Tour) -> Self:
        DATE_MIN = datetime(2023, 8, 1, 0, 0, 0, 0)
        DATE_MAX = datetime(2023, 11, 1, 0, 0, 0, 0)

        departure_epoch = DATE_MIN.timestamp() + random.randint(0, DATE_MAX.timestamp() - DATE_MIN.timestamp())
        arrival_epoch = departure_epoch + 60 * 60 * 24 * random.randint(4, 14)
        adults = random.randint(2, 8
                                   if tour.metadata.max_adults is None
                                   else tour.metadata.max_adults)
        kids = random.randint(0, adults // 2
                                 if tour.metadata.max_kids is None
                                 else tour.metadata.max_kids)
        return Offer(
            arrival_date=datetime.fromtimestamp(arrival_epoch),
            departure_date=datetime.fromtimestamp(departure_epoch),
            transport=random.choice(tour.metadata.transport_type)
                      if tour.metadata.transport_type is not []
                      else "plane",
            number_of_adults=adults,
            number_of_kids=kids,
            room_type=random.choice(tour.metadata.room_type)
                      if len(tour.metadata.room_type) > 0 else
                      "standard"
        )


def drop_and_create_tables(cursor):
    cursor.execute(
        "DROP TABLE IF EXISTS Offer"
    )
    cursor.execute(
        "DROP TABLE IF EXISTS Tour"
    )
    cursor.execute(
        '''
CREATE TABLE Tour (
    id bigserial primary key,
    operator varchar(128) not null,
    hotel varchar(128) not null,
    country varchar(128) not null,
    city varchar(256) not null,
    description text,
    thumbnail_url varchar(256) not null,
    score smallint not null
)
        '''.strip()
    )

    cursor.execute(
        '''
CREATE TABLE Offer (
    id bigserial primary key,
    tour_id bigserial references Tour (id),
    arrival_date date not null,
    departure_date date not null,
    transport varchar(128) not null,
    number_of_kids smallint not null,
    number_of_adults smallint not null,
    room_type varchar(128) not null,
    available boolean not null default true,

    constraint valid_kids
        check (number_of_kids >= 0),
    constraint valid_adults
        check (number_of_adults >= 0)
);
        '''.strip()
    )

def load_rainbow_tours() -> list[Tour]:
    RAINBOW_PLANE = "rainbow/json_corrected/rainbow_scrapped_data_plane.json"
    RAINBOW_SELF = "rainbow/json_corrected/rainbow_scrapped_data_self.json"

    tours = []

    for trans, f_path in [
        ("plane", RAINBOW_PLANE),
        ("self", RAINBOW_SELF)
    ]:
        with open(f_path, "r") as f:
            for raw_tour in json.load(f):
                tours.append(Tour(
                    operator=raw_tour["operator"],
                    hotel=raw_tour["hotel"],
                    country=raw_tour["country"],
                    city=raw_tour["city"],
                    description=raw_tour["description"],
                    thumbnail_url=raw_tour["img"],
                    score=float(raw_tour["score"]),
                    metadata=TourMetadata(
                        transport_type=[trans],
                        room_type=(
                            ["standard"] if raw_tour["room"]["is_standard"] else []
                            +
                            ["family"] if raw_tour["room"]["is_family"] else []
                            +
                            ["apartment"] if raw_tour["room"]["is_apartment"] else []
                            +
                            ["studio"] if raw_tour["room"]["is_studio"] else []
                        ),
                    )
                ))

    return tours

def load_itaka_tours():
    TOURS_PATH = "scrappers/itaka/itaka_offers.json"

    tours = []

    with open(TOURS_PATH, "r") as f:
       for raw_tour in json.load(f):
           tours.append(Tour(
               operator=raw_tour["operator"],
               hotel=raw_tour["hotel"],
               country=raw_tour["country"],
               city=raw_tour["city"],
               description=raw_tour["description"],
               thumbnail_url=raw_tour["img"],
               score=float(raw_tour["score"]),
               metadata=TourMetadata(
                   transport_type=["plane"],
                   room_type=(
                       ["standard"] if raw_tour["room"]["is_standard"] else []
                       +
                       ["family"] if raw_tour["room"]["is_family"] else []
                       +
                       ["apartment"] if raw_tour["room"]["is_apartment"] else []
                       +
                       ["studio"] if raw_tour["room"]["is_studio"] else []
                   ),
               )
           ))

    return tours

def load_tui_tours():
    TOURS_PATH = "tui/tui.json"
    ROOM_SIZES = {
        "small": 2,
        "medium": 5,
        "large": 8,
    }

    tours = []

    with open(TOURS_PATH, "r") as f:
       for raw_tour in json.load(f):
           tours.append(Tour(
               operator=raw_tour["operator"],
               hotel=raw_tour["hotel"],
               country=raw_tour["country"],
               city=raw_tour["city"],
               description=raw_tour["description"],
               thumbnail_url=raw_tour["image"],
               score=float(raw_tour["score"]),
               metadata=TourMetadata(
                   transport_type=["plane"] if raw_tour["transport"]["organised"] else ["self"],
                   room_type=(
                       ["family"] if raw_tour["kids"] else []
                       +
                       ["apartment"] if raw_tour["room"]["is_apartament"] else []
                       +
                       ["studio"] if raw_tour["room"]["is_studio"] else []
                   ),
                   max_kids=ROOM_SIZES[raw_tour["room"]["size"]] // 2,
                   max_adults=ROOM_SIZES[raw_tour["room"]["size"]],
               )
           ))

    return tours

def postprocess_tours(tours: list[Tour]):
    def _postprocess(tour: Tour):
        if "family" not in tour.metadata.room_type:
            tour.metadata.max_kids = 0
        return tour

    def _check_valid(tour: Tour):
        return (
            tour.city is not None and
            tour.country is not None and
            tour.hotel is not None and
            tour.description is not None and
            tour.score is not None and
            tour.thumbnail_url is not None
        )

    return [
        _postprocess(tour)
        for tour in tours
        if _check_valid(tour)
    ]


def main():
    tours = (
        load_rainbow_tours() +
        load_itaka_tours() +
        load_tui_tours()
    )
    tours = postprocess_tours(tours)
    print(f"Inserting {len(tours)} new records ...")
    with pg.connect("dbname=rsww user=postgres password=postgres host=localhost port=5432") as conn:
        with conn.cursor() as curr:
            drop_and_create_tables(curr)
            for tour in tours:
                tour_id = tour.insert_into_db(curr, "Tour")
                for _ in range(0, random.randint(1, 3)):
                    Offer.random_from_tour(tour).insert_into_db(
                        curr,
                        tour_id
                    )
        conn.commit()

if __name__ == "__main__":
    main()