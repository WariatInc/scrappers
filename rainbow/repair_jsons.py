# This script compair two json results and repair them

import json
import re
import os
import urllib.request
from PIL import Image

file1 = open('json/rainbow_scrapped_data_plane2_2.json')
file2 = open('json/rainbow_scrapped_data_plane2_3.json')

CORRECTION_OFFER_NAME = 'rainbow_scrapped_data_plane'
READY_OFFER_NAME = 'rainbow_scrapped_data_plane2_3_ready'


def compare_two_files(file_first, file_second):
    offers_one = json.load(file_first)
    offers_second = json.load(file_second)

    offers_result = offers_second.copy()

    for i, offer in enumerate(offers_one):
        result = next(filter(lambda d: d.get('hotel') == offer['hotel'], offers_second), None)
        index = offers_result.index(result)
        # index2 = next((i2 for i2, d in enumerate(offers_second) if offer['hotel'] == d['hotel']))
        if 'gif' in offers_result[index]['image'] and len(offer['images']) > 1:
            offers_result[index].update({'image': offer['images'][0]})
        if 'Not found' in offers_result[index]['description']:
            offers_result[index].update({'description': offer['description']})

    _ = [offers_result.remove(d) for d in offers_result if d['description'] == "Not found"]
    offers_result = [d for d in offers_result if d.get('description') != 'Not found']
    offers_result = [d for d in offers_result if 'gif' not in d.get('image')]

    print(len(offers_result))
    return offers_result


def modify_img_name(name, index):
    name = re.sub(r'\s+', '_', name.strip())
    # remove all other characters except alphanumeric and underscores
    name = re.sub(r'[^\w_]', '', name.lower())
    # append .jpg extension
    return index + "_" + name + '.jpg'


def save_images(offers_results):
    os.makedirs(f'images/{CORRECTION_OFFER_NAME}', exist_ok=True)

    for i, offer in enumerate(offers_results):
        # full_path = os.path.join("images", FINAL_OFFER_NAME, modify_img_name(offer['hotel']))
        full_path = os.path.join("images", CORRECTION_OFFER_NAME, modify_img_name(offer['hotel'], str(i)))
        image_url = "http:" + offer['image']
        urllib.request.urlretrieve(image_url, full_path)
        # check if the download was successful
        response = urllib.request.urlopen(image_url)

        if response.getcode() == 200:
            pass
        else:
            print(f"{offer['hotel']} Image download failed.")

        offer.update({'image_path': full_path})
    return offers_results


def resize_images():
    # loop over all files in the directory
    for filename in os.listdir(f"images/{CORRECTION_OFFER_NAME}"):
        if filename.endswith(".jpg"):
            # load the image
            img_path = os.path.join("images", CORRECTION_OFFER_NAME, filename)
            img = Image.open(img_path)

            # check if the image is larger than 410x225
            if img.width > 410 or img.height > 225:
                # resize the image to 410x225
                img = img.resize((410, 225))

                # save the resized image
                img.save(img_path)


# final_offers = compare_two_files(file1, file2)
# final_offers = save_images(final_offers)


# with open(f'json_corrected/{FINAL_OFFER_NAME}.json', 'w') as f:
#     json.dump(final_offers, f)

# resize_images()

final_file = open(f'json_corrected/{CORRECTION_OFFER_NAME}.json')
final_offers = json.load(final_file)

for offer in final_offers:
    offer.update({
        'room': {
            'is_standard': True,
            'is_family': any(map(lambda x: "family" in x.lower() or "junior" in x.lower() or "rodzinny" in x.lower(),
                                 offer['room_types'])),
            'is_apartment': any(
                map(lambda
                        x: "deluxe" in x.lower() or "premium" in x.lower() or "apartment" in x.lower() or "apartament" in x.lower(),
                    offer['room_types'])),
            'is_studio': any(map(lambda x: "superior" in x.lower() or "economy" in x.lower() or "studio" in x.lower(),
                                 offer['room_types']))
        }
    })

    offer.update(
        {
            'image_path': re.sub(r'\\rainbow_scrapped_data_plane', '', offer['image_path'])
        }
    )
    offer.pop('image')
    offer.pop('link')
    offer.pop('room_types')

with open(f'json_corrected/{READY_OFFER_NAME}.json', 'w') as f:
    json.dump(final_offers, f)