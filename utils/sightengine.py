import requests
import json


def request_sightengine(image_full_path: str) -> dict:
    """向 Sightengine API 发送图片进行审查"""
    params = {
    'models': 'nudity-2.1,gore-2.0',
    'api_user': '1908461751',
    'api_secret': 'JxmEGZ6tebu7Lo3W5gCJNYxBjqQXYva6'
    }
    files = {'media': open(image_full_path, 'rb')}
    r = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)

    return json.loads(r.text)

"""Example response from Sightengine API:
{
    "status": "success",
    "request": {
        "id": "req_iVQCwEI5F6MipwJwM4XAG",
        "timestamp": 1753965278.977497,
        "operations": 2
    },
    "nudity": {
        "sexual_activity": 0.001,
        "sexual_display": 0.001,
        "erotica": 0.001,
        "very_suggestive": 0.001,
        "suggestive": 0.001,
        "mildly_suggestive": 0.001,
        "suggestive_classes": {
            "bikini": 0.001,
            "cleavage": 0.001,
            "cleavage_categories": {
                "very_revealing": 0.001,
                "revealing": 0.001,
                "none": 0.99
            },
            "lingerie": 0.001,
            "male_chest": 0.001,
            "male_chest_categories": {
                "very_revealing": 0.001,
                "revealing": 0.001,
                "slightly_revealing": 0.001,
                "none": 0.99
            },
            "male_underwear": 0.001,
            "miniskirt": 0.001,
            "minishort": 0.001,
            "nudity_art": 0.001,
            "schematic": 0.001,
            "sextoy": 0.001,
            "suggestive_focus": 0.001,
            "suggestive_pose": 0.001,
            "swimwear_male": 0.001,
            "swimwear_one_piece": 0.001,
            "visibly_undressed": 0.001,
            "other": 0.001
        },
        "none": 0.99,
        "context": {
            "sea_lake_pool": 0.6,
            "outdoor_other": 0.4,
            "indoor_other": 0.001
        }
    },
    "gore": {
        "prob": 0.001,
        "classes": {
            "very_bloody": 0.001,
            "slightly_bloody": 0.001,
            "body_organ": 0.001,
            "serious_injury": 0.001,
            "superficial_injury": 0.001,
            "corpse": 0.001,
            "skull": 0.001,
            "unconscious": 0.001,
            "body_waste": 0.001,
            "other": 0.001
        },
        "type": {
            "animated": 0.001,
            "fake": 0.001,
            "real": 0.001
        }
    },
    "media": {
        "id": "med_iVQCZgK7uYxSvErv7XrKk",
        "uri": "https://sightengine.com/assets/img/examples/example7.jpg"
    }
}
"""