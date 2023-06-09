"""
This script is repsonsible for updating prices in MongoDB read store,
so that is has correct `Offer` prices.
"""

from datetime import datetime
from math import ceil
from functools import lru_cache

from pymongo import MongoClient
from pymongo.collection import Collection
import tqdm

ROOM_TYPE_MULTIPLIER = {
    "family": 1.5,
    "studio": 0.75,
    "apartment": 2.5,
}

KIDS_FLIGHT_DISCOUNT = 0.85
KIDS_HOTEL_DISCOUNT = 0.8
PROVISION = 0.1


class Mongo:
    def __init__(self) -> None:
        client = MongoClient("mongodb://mongodb_admin:mongodb@localhost:27017")
        db = client.trip_offer_mongo

        self.offer: Collection = db.Offer
        self.tour: Collection = db.Tour
        self.tour.create_index("id", unique=True)
        self.offer.create_index("id", unique=True)
    
    @lru_cache
    def get_tour(self, id: str):
        return self.tour.find_one({"id": id})


def calculate_price(tour: dict, offer: dict) -> float:
    arrival_date: datetime = tour["arrival_date"]
    departure_date: datetime = tour["departure_date"]
    price_per_night = tour["average_night_cost"]
    flight_cost = tour["average_flight_cost"]
    all_inclusive = offer["all_inclusive"]
    breakfast = offer["breakfast"]
    kids = offer["number_of_kids"]
    adults = offer["number_of_adults"]
    room_type = offer["room_type"]
    is_flight = tour["transport"] == "plane"

    days = (departure_date - arrival_date).days

    # Hotel price
    extras = 0.0
    if all_inclusive:
        extras += 0.15 * price_per_night
    if breakfast:
        extras += 0.5 * price_per_night

    hotel_price = (
        (price_per_night * ROOM_TYPE_MULTIPLIER.get(room_type, 1) + extras)
        * days
        * (adults + kids * KIDS_HOTEL_DISCOUNT)
    )

    # Flight price
    flight_price = 0.0

    if is_flight:
        flight_price = flight_cost * 2 * (adults + kids * KIDS_FLIGHT_DISCOUNT)

    # Apply provision
    total_price = ceil((1 + PROVISION) * (flight_price + hotel_price)) - 0.01

    return round(total_price, 2)


def main():
    mongo = Mongo()

    offer_amount = mongo.offer.count_documents({})

    prices: dict[str, float] = {}

    for offer in tqdm.tqdm(mongo.offer.find({}), desc="Calculating prices ...", total=offer_amount):
        if "price" in offer:
            continue

        tour_id = offer["tour_id"]
        offer_id = offer["id"]

        tour = mongo.get_tour(tour_id)
        assert isinstance(tour, dict)
        price = calculate_price(tour, offer)

        prices[offer_id] = price
    
    for offer_id, price in tqdm.tqdm(prices.items(), desc="Updating MongoDB"):
        mongo.offer.update_one({"id": offer_id}, {"$set": {"price": price}})

if __name__ == "__main__":
    main()
