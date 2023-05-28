from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Self
import uuid
import random
import json

from merger.utils import random_between
from merger.const import (
    AVERAGE_FLIGHT_COST_PER_COUNTRY,
    AVERAGE_NIGHT_COST_PER_COUNTRY
)


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
    description: str
    thumbnail_url: str

    metadata: TourMetadata
    id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())

    # Semi-Randomized fields
    arrival_date: Optional[datetime] = None
    departute_date: Optional[datetime] = None
    departure_city: Optional[str] = None
    transport: Optional[str] = None
    average_night_cost: Optional[float] = None
    average_flight_cost: Optional[float] = None

    def __post_init__(self):
        DATE_MIN = datetime(2023, 8, 1, 0, 0, 0, 0)
        DATE_MAX = datetime(2023, 11, 1, 0, 0, 0, 0)

        arrival_epoch = DATE_MIN.timestamp() + random.randint(
            0, DATE_MAX.timestamp() - DATE_MIN.timestamp()
        )
        departure_epoch = arrival_epoch + 60 * 60 * 24 * random.randint(4, 14)

        self.arrival_date = datetime.fromtimestamp(arrival_epoch)
        self.departure_date = datetime.fromtimestamp(departure_epoch)
        self.transport = (
            random.choice(self.metadata.transport_type)
            if self.metadata.transport_type is not []
            else "plane"
        )
        self.average_night_cost = (
            round(
                AVERAGE_NIGHT_COST_PER_COUNTRY[self.country] * random_between(0.9, 1.1),
                2,
            )
            if self.country in AVERAGE_NIGHT_COST_PER_COUNTRY
            else None
        )
        self.average_flight_cost = (
            round(
                AVERAGE_FLIGHT_COST_PER_COUNTRY[self.country]
                * random_between(0.9, 1.1),
                2,
            )
            if self.country in AVERAGE_FLIGHT_COST_PER_COUNTRY
            else None
        )
        self.departure_city = (
            None if self.transport == "self" else random.choice(CITIES)
        )

    def random_clone(self) -> Self:
        return Tour(
            operator=self.operator,
            hotel=self.hotel,
            country=self.country,
            city=self.city,
            description=self.description,
            thumbnail_url=self.thumbnail_url,
            metadata=self.metadata,
        )


@dataclass
class Offer:
    number_of_adults: int
    number_of_kids: int
    room_type: str
    all_inclusive: bool
    breakfast: bool
    id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())

    @staticmethod
    def random_from_tour(tour: Tour) -> Self:
        adults = random.randint(
            1, 6 if tour.metadata.max_adults is None else tour.metadata.max_adults
        )
        kids = random.randint(
            0, adults // 2 if tour.metadata.max_kids is None else tour.metadata.max_kids
        )
        all_inclusive, breakfast = random.choice(
            [
                (False, False),
                (True, False),
                (False, True),
            ]
        )
        return Offer(
            number_of_adults=adults,
            number_of_kids=kids,
            all_inclusive=all_inclusive,
            breakfast=breakfast,
            room_type=random.choice(tour.metadata.room_type)
            if len(tour.metadata.room_type) > 0
            else "standard",
        )


def load_rainbow_tours() -> list[Tour]:
    RAINBOW_PLANE = "rainbow/json_corrected/rainbow_scrapped_data_plane.json"
    RAINBOW_SELF = "rainbow/json_corrected/rainbow_scrapped_data_self.json"

    tours = []

    for trans, f_path in [("plane", RAINBOW_PLANE), ("self", RAINBOW_SELF)]:
        with open(f_path, "r") as f:
            for raw_tour in json.load(f):
                tours.append(
                    Tour(
                        operator=raw_tour["operator"],
                        hotel=raw_tour["hotel"],
                        country=raw_tour["country"],
                        city=raw_tour["city"],
                        description=raw_tour["description"],
                        thumbnail_url=raw_tour["img"],
                        metadata=TourMetadata(
                            transport_type=[trans],
                            room_type=(
                                ["standard"]
                                if raw_tour["room"]["is_standard"]
                                else [] + ["family"]
                                if raw_tour["room"]["is_family"]
                                else [] + ["apartment"]
                                if raw_tour["room"]["is_apartment"]
                                else [] + ["studio"]
                                if raw_tour["room"]["is_studio"]
                                else []
                            ),
                        ),
                    )
                )

    return tours


def load_itaka_tours():
    TOURS_PATH = "scrappers/itaka/itaka_offers.json"

    tours = []

    with open(TOURS_PATH, "r") as f:
        for raw_tour in json.load(f):
            tours.append(
                Tour(
                    operator=raw_tour["operator"],
                    hotel=raw_tour["hotel"],
                    country=raw_tour["country"],
                    city=raw_tour["city"],
                    description=raw_tour["description"],
                    thumbnail_url=raw_tour["img"],
                    metadata=TourMetadata(
                        transport_type=["plane"],
                        room_type=(
                            ["standard"]
                            if raw_tour["room"]["is_standard"]
                            else [] + ["family"]
                            if raw_tour["room"]["is_family"]
                            else [] + ["apartment"]
                            if raw_tour["room"]["is_apartment"]
                            else [] + ["studio"]
                            if raw_tour["room"]["is_studio"]
                            else []
                        ),
                    ),
                )
            )

    return tours


def load_tui_tours():
    TOURS_PATH = "tui/tui.json"
    ROOM_SIZES = {
        "small": 2,
        "medium": 4,
        "large": 6,
    }

    tours = []

    with open(TOURS_PATH, "r") as f:
        for raw_tour in json.load(f):
            tours.append(
                Tour(
                    operator=raw_tour["operator"],
                    hotel=raw_tour["hotel"],
                    country=raw_tour["country"],
                    city=raw_tour["city"],
                    description=raw_tour["description"],
                    thumbnail_url=raw_tour["image"],
                    metadata=TourMetadata(
                        transport_type=["plane"]
                        if raw_tour["transport"]["organised"]
                        else ["self"],
                        room_type=(
                            ["family"]
                            if raw_tour["kids"]
                            else [] + ["apartment"]
                            if raw_tour["room"]["is_apartament"]
                            else [] + ["studio"]
                            if raw_tour["room"]["is_studio"]
                            else []
                        ),
                        max_kids=ROOM_SIZES[raw_tour["room"]["size"]] // 2,
                        max_adults=ROOM_SIZES[raw_tour["room"]["size"]],
                    ),
                )
            )

    return tours


def fill_tours(original_tours: list[Tour], up_to_size: int) -> list[Tour]:
    return [random.choice(original_tours).random_clone() for _ in range(up_to_size)]


def postprocess_tours(tours: list[Tour]):
    def _postprocess(tour: Tour):
        if "family" not in tour.metadata.room_type:
            tour.metadata.max_kids = 0
        return tour

    def _check_valid(tour: Tour):
        return (
            tour.city is not None
            and tour.country is not None
            and tour.hotel is not None
            and tour.description is not None
            and tour.thumbnail_url is not None
        )

    return [_postprocess(tour) for tour in tours if _check_valid(tour)]
