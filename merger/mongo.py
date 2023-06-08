from pymongo import MongoClient
import tqdm

from merger.types import Tour, Offer
from merger.utils import run_cmd


def tour_to_dict(tour: Tour) -> dict:
    return dict(
        id=str(tour.id),
        operator=tour.operator,
        hotel=tour.hotel,
        country=tour.country,
        city=tour.city,
        departure_city=tour.departure_city,
        description=tour.description,
        thumbnail_url=tour.thumbnail_url,
        arrival_date=tour.arrival_date,
        departure_date=tour.departure_date,
        transport=tour.transport,
        average_night_cost=tour.average_night_cost,
        average_flight_cost=tour.average_flight_cost,
    )


def offer_to_dict(offer: Offer, tour_id: int) -> dict:
    return dict(
        id=str(offer.id),
        tour_id=str(tour_id),
        number_of_adults=offer.number_of_adults,
        number_of_kids=offer.number_of_kids,
        room_type=offer.room_type,
        all_inclusive=offer.all_inclusive,
        breakfast=offer.breakfast,
        is_available=True,
    )


def setup(tours_and_offers: list[tuple[Tour, list[Offer]]]):
    client = MongoClient("mongodb://mongodb_admin:mongodb@localhost:27017")

    db = client.rsww
    offer_collection = db["Offer"]
    tour_collection = db["Tour"]
    offer_collection.drop()
    tour_collection.drop()

    for tour, offers in tqdm.tqdm(tours_and_offers, desc="Populating mongo ..."):
        tour_collection.insert_one(tour_to_dict(tour))
        for offer in offers:
            offer_collection.insert_one(offer_to_dict(offer, tour.id))

    db["OfferView"].drop()
    db.command(
        {
            "create": "OfferView",
            "viewOn": "Offer",
            "pipeline": [
                {
                    "$lookup": {
                        "from": "Tour",
                        "localField": "tour_id",
                        "foreignField": "id",
                        "as": "tour",
                    }
                },
                {"$project": {"_id": 0}},
                {"$unwind": "$tour"},
            ],
        }
    )


def dump():
    run_cmd("mongodump mongodb://mongodb_admin:mongodb@localhost:27017")
    run_cmd("mv dump/rsww ./rsww")
    run_cmd("zip -r dumps/mongodb_dump.zip ./rsww/*")
    run_cmd("rm -r ./dump ./rsww")
