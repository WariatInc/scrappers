import random

import tqdm

from merger.const import *
from merger.types import (
    load_itaka_tours,
    load_rainbow_tours,
    load_tui_tours,
    postprocess_tours,
    fill_tours,
    Offer
)
from merger import postgres, mongo


def main():
    print("Loading tours ...")
    tours = load_rainbow_tours() + load_itaka_tours() + load_tui_tours()
    tours = fill_tours(tours, 20_000)
    print("Postprocessing tours ...")
    tours = postprocess_tours(tours)
    tours_and_offers = [
        (tour, [Offer.random_from_tour(tour) for _ in range(1, random.randint(20, 50))])
        for tour in tqdm.tqdm(tours, "Generating offers ...")
    ]

    offers_amount = sum((len(offers) for (_, offers) in tours_and_offers))

    print(f"Inserting {offers_amount} new records into mongo ...")
    mongo.setup(tours_and_offers)
    print(f"Inserting {offers_amount} new records into postgres ...")
    postgres.setup(tours_and_offers)
    postgres.dump()


if __name__ == "__main__":
    main()
