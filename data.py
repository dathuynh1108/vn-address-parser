import os
import json


# Read from new_address.json
def load_new_address():
    json_file_path = os.path.join("data", "new_address.json")
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            address_data = json.load(f)

        # Create a dictionary grouped by province for faster lookup
        address_dict = {}
        for item in address_data:
            province = item["province"]
            ward = item["ward"]

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
            province = item["province"]
            district = item["district"]

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
    ("con tum"): "Kon Tum",
    ("za lai"): "Gia Lai",
    ("tt hue", "thua thien hue"): "Thừa Thiên - Huế",
}

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

