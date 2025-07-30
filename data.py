import os
import json
from utils import normalize_string

# Read from new_address.json
def load_new_address():
    json_file_path = os.path.join("data", "new_address.json")
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            address_data = json.load(f)

        # Create a dictionary grouped by province for faster lookup
        address_dict = {}
        for item in address_data:
            province = normalize_string(item["province"])
            ward = normalize_string(item["ward"])

            if province not in address_dict:
                address_dict[province] = []
            address_dict[province].append(ward)

        return address_dict
    except FileNotFoundError:
        print(f"File {json_file_path} not found")
        return {}
    except json.JSONDecodeError:
        print(f"Invalid JSON in {json_file_path}")
        return {}


def load_old_address():
    json_file_path = os.path.join("data", "old_address.json")
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            address_data = json.load(f)

        # Create a dictionary grouped by province for faster lookup
        address_dict = {}
        for item in address_data:
            province = normalize_string(item["province"])
            district = normalize_string(item["district"])

            if province not in address_dict:
                address_dict[province] = []
            address_dict[province].append(district)

        return address_dict
    except FileNotFoundError:
        print(f"File {json_file_path} not found")
        return {}
    except json.JSONDecodeError:
        print(f"Invalid JSON in {json_file_path}")
        return {}


SPECIAL_PROVINCE_MAP = {
    ("br vt", "br-vt", "brvt", "ba ria vung tau"): "Bà Rịa - Vũng Tàu",
    (
        "dac lac",
        "dac lak",
        "dak lak",
        "dak lac",
        "daklak",
        "daklac",
        "daclac",
    ): "ĐắkLắk",
    ("con tum",): "Kon Tum",
    ("za lai",): "Gia Lai",
    ("tt hue", "thua thien hue"): "Thừa Thiên - Huế",
}

SPECIAL_PROVINCE_MAP_FULL = {}
for cases, map_province in SPECIAL_PROVINCE_MAP.items():
    for case in cases:
        SPECIAL_PROVINCE_MAP_FULL[case] = map_province

DASH_CASES = [
    ("bà rịa", "vũng tàu"),
    ("sao bọng", "đăng hà"),
    ("phan rang", "tháp chàm"),
    ("thừa thiên", "huế"),
    ("xuân hương", "đà lạt"),
    ("cam ly", "đà lạt"),
    ("xuân trường", "đà lạt"),
    ("lang biang", "đà lạt"),
]

NEW_ADDRESS = load_new_address()
OLD_ADDRESS = load_old_address()

VN_PROVINCES_SET = set()

for province in OLD_ADDRESS.keys():
    VN_PROVINCES_SET.add(province)
 
for province in NEW_ADDRESS.keys():
    VN_PROVINCES_SET.add(province)