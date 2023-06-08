import uuid
import tqdm

import psycopg2 as pg

from merger.types import Tour, Offer
from merger.utils import run_cmd


def drop_and_create_tables(cursor):
    cursor.execute("DROP TABLE IF EXISTS Offer")
    cursor.execute("DROP TABLE IF EXISTS Tour")
    cursor.execute(
        """
CREATE TABLE Tour (
    id uuid primary key,
    operator varchar(128) not null,
    hotel varchar(128) not null,
    country varchar(128) not null,
    city varchar(256) not null,
    departure_city varchar(256),
    description text,
    thumbnail_url varchar(256) not null,
    arrival_date date not null,
    departure_date date not null,
    transport varchar(128) not null,
    average_night_cost real not null,
    average_flight_cost real,

    constraint valid_cost1
        check (average_night_cost > 0),
    constraint valid_cost2
        check (average_flight_cost > 0)
)
        """.strip()
    )

    cursor.execute(
        """
CREATE TABLE Offer (
    id uuid primary key,
    tour_id uuid references Tour (id),
    number_of_kids smallint not null,
    number_of_adults smallint not null,
    room_type varchar(128) not null,
    all_inclusive boolean not null,
    breakfast boolean not null,
    available boolean not null default true,

    constraint valid_kids
        check (number_of_kids >= 0),
    constraint valid_adults
        check (number_of_adults >= 0)
);
        """.strip()
    )


def insert_offer(cursor, offer: Offer, tour_id: uuid.UUID, table_name: str = "Offer"):
    cursor.execute(
        f"INSERT INTO {table_name} (id, tour_id, number_of_kids, number_of_adults, room_type, all_inclusive, breakfast) VALUES %s RETURNING id",
        (
            (
                str(offer.id),
                str(tour_id),
                offer.number_of_kids,
                offer.number_of_adults,
                offer.room_type,
                offer.all_inclusive,
                offer.breakfast,
            ),
        ),
    )


def insert_tour(cursor, tour: Tour, table_name: str = "Tour"):
    cursor.execute(
        f"INSERT INTO {table_name} (id, operator, hotel, country, city, departure_city, description, thumbnail_url, arrival_date, departure_date, transport, average_night_cost, average_flight_cost) VALUES %s RETURNING id",
        (
            (
                str(tour.id),
                tour.operator,
                tour.hotel,
                tour.country,
                tour.city,
                tour.departure_city,
                tour.description,
                tour.thumbnail_url,
                tour.arrival_date,
                tour.departure_date,
                tour.transport,
                tour.average_night_cost,
                tour.average_flight_cost,
            ),
        ),
    )


def setup(tours_and_offers: list[tuple[Tour, list[Offer]]]):
    with pg.connect(
        "dbname=rsww user=postgres password=postgres host=localhost port=5432"
    ) as conn:
        with conn.cursor() as curr:
            drop_and_create_tables(curr)
            for tour, offers in tqdm.tqdm(
                tours_and_offers, desc="Populating postgres ..."
            ):
                insert_tour(curr, tour)
                for offer in offers:
                    insert_offer(curr, offer, tour.id)
        conn.commit()


def dump():
    run_cmd(
        "pg_dump -d rsww -h localhost -p 5432 -U postgres -Z 5 -Fc -f dumps/postgres_to.gz"
    )
