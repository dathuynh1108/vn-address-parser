import re
from fuzzywuzzy import fuzz, process
from utils import normalize_vietnamese, normalize_string, has_number
from data import NEW_ADDRESS, OLD_ADDRESS, SPECIAL_PROVINCE_MAP_FULL, DASH_CASES, VN_PROVINCES_SET
from copy import copy

VN_PROVINCE_DISTRICT_DICT = dict()
VN_PROVINCE_WARD_DICT = dict()

for province, districts in OLD_ADDRESS.items():
    province_normalized = normalize_vietnamese(province)
    
    clone = copy(districts)
    
    VN_PROVINCE_DISTRICT_DICT[province] = clone
    VN_PROVINCE_DISTRICT_DICT[province_normalized] = VN_PROVINCE_DISTRICT_DICT[province]
    
    for district in districts:
        district_normalied = normalize_vietnamese(district)
        VN_PROVINCE_DISTRICT_DICT[province].append(district_normalied)

for province, wards in NEW_ADDRESS.items():
    province_normalized = normalize_vietnamese(province)
    clone = copy(wards)
    
    VN_PROVINCE_WARD_DICT[province] = clone
    VN_PROVINCE_WARD_DICT[province_normalized] = VN_PROVINCE_WARD_DICT[province]
    
    for ward in wards:
        ward_normalized = normalize_vietnamese(ward)
        VN_PROVINCE_WARD_DICT[province].append(ward_normalized)


VN_PROVINCES_NORMALIZED_SET = {
    normalize_vietnamese(province) for province in VN_PROVINCES_SET
}

PROVINCE_LOOKUP = VN_PROVINCES_SET
PROVINCE_LOOKUP.update(VN_PROVINCES_NORMALIZED_SET)

# Also create a set of all wards for faster searching
ALL_WARDS_SET = set()
for province, wards in NEW_ADDRESS.items():
    for ward in wards:
        ALL_WARDS_SET.add(normalize_string(ward))

ALL_WARDS_SET_NORMALIZED = {normalize_vietnamese(ward) for ward in ALL_WARDS_SET}

DISTRICTS_SET = set()
for province, districts in OLD_ADDRESS.items():
    for district in districts:
        DISTRICTS_SET.add(normalize_string(district))

DISTRICTS_SET_NORMALIZED = {normalize_vietnamese(district) for district in DISTRICTS_SET}

DISTRICT_PREFIX_REGEX = re.compile(
    r"^(?:q\.?\s?\d*|quan|quận|h\.?\s?|huyen|huyện|tp\.?|t\.p\.?|thanh pho|thành phố|thi xa|thị xã|tx\.?\s?)\b\.?,?\s*",
    flags=re.IGNORECASE,
)

WARD_PREFIX_REGEX = re.compile(
    r"^(?:p\.?\s?\d*|phuong|phường|xa|xã|x\.?|đặc khu|dac khu|dk\.?|thi tran|thị trấn|tt\.?|khu pho|khu phố|kp\.?)\b\.?,?\s*",
    flags=re.IGNORECASE,
)

PROVINCE_PREFIX_REGEX = re.compile(
    r"^(?:tp\.?\s?|t\.?\s?|thanh pho|thành phố|tinh|tỉnh)\b\.?,?\s*",
    flags=re.IGNORECASE,
)

BUILDING_PREFIXES = {"ct", "hh", "bt", "ps", "ls", "cd"}  # , 'n'}


# Create normalized versions of DASH_CASES for better matching
DASH_CASES_NORMALIZED = [
    (normalize_vietnamese(case[0]).lower(), normalize_vietnamese(case[1]).lower())
    for case in DASH_CASES
]


def handle_dash(str):
    if "-" not in str:
        return str
    else:
        sub_str_list = str.split("-")
        new_str = ""
        for i, sub_str in enumerate(sub_str_list):
            if i != len(sub_str_list) - 1:
                try:
                    substr_before_dash = sub_str.strip().split(" ")[-1]
                    substr_before_dash = "".join(
                        e for e in substr_before_dash if e.isalnum()
                    )

                    substr_after_dash = sub_str_list[i + 1].strip().split(" ")[0]
                    substr_after_dash = "".join(
                        e for e in substr_after_dash if e.isalnum()
                    )

                except IndexError:
                    return ""

                # Check if this dash case should be preserved
                should_keep_dash = False

                # Check against DASH_CASES (both original and normalized)
                current_part_lower = sub_str.lower()
                next_part_lower = sub_str_list[i + 1].lower()
                current_part_normalized = normalize_vietnamese(sub_str).lower()
                next_part_normalized = normalize_vietnamese(sub_str_list[i + 1]).lower()

                for case_orig, case_norm in zip(DASH_CASES, DASH_CASES_NORMALIZED):
                    # Check original cases
                    if (
                        case_orig[0].lower() in current_part_lower
                        and case_orig[1].lower() in next_part_lower
                    ):
                        should_keep_dash = True
                        break

                    # Check normalized cases
                    if (
                        case_norm[0] in current_part_normalized
                        and case_norm[1] in next_part_normalized
                    ):
                        should_keep_dash = True
                        break

                # Original logic for other cases
                if (
                    should_keep_dash
                    or (
                        has_number(substr_before_dash) and has_number(substr_after_dash)
                    )
                    or (
                        len(substr_after_dash) <= 2
                        and substr_after_dash.lower() not in BUILDING_PREFIXES
                    )
                ):
                    new_str += sub_str + "-"
                else:
                    new_str += sub_str + ","
            else:
                new_str += sub_str
        return new_str


def fuzzy_search_province(part, fuzzy_threshold=80):
    part_normalized_string = normalize_string(part)
    part_normalized_vietnamese = normalize_vietnamese(part)

    result = process.extractOne(
        part_normalized_vietnamese,
        list(SPECIAL_PROVINCE_MAP_FULL.keys()),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print(
            "Found province with special case:", matched_key,
            SPECIAL_PROVINCE_MAP_FULL[matched_key],
            "Score:",
            score,
        )
        return SPECIAL_PROVINCE_MAP_FULL[matched_key]

    # Find best match, with accentive fuzzy matching
    result = process.extractOne(
        part_normalized_string,
        list(PROVINCE_LOOKUP),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )

    if result:
        matched_key, score = result
        print("Found province with accent:", matched_key, "Score:", score)
        return matched_key

    result = process.extractOne(
        part_normalized_vietnamese,
        list(PROVINCE_LOOKUP),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print("Found province with unaccent:", matched_key, "Score:", score)
        return matched_key

    return None

def fuzzy_search_ward(part, ward_set = None, fuzzy_threshold=80):    
    if ward_set is None:
        print("No ward set provided. Using all wards.")
        ward_set = ALL_WARDS_SET.copy()
        ward_set.update(ALL_WARDS_SET_NORMALIZED)
    
    part_normalized_string = normalize_string(part)
    part_normalized_vietnamese = normalize_vietnamese(part)

    result = process.extractOne(
        part_normalized_string,
        list(ward_set),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print("Found ward with accent:", matched_key, "Score:", score)
        return matched_key

    result = process.extractOne(
        part_normalized_vietnamese,
        list(ward_set),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print("Found ward with unaccent:", matched_key, "Score:", score)
        return matched_key
    
    return None

def fuzzy_search_district(part, district_set = None, fuzzy_threshold=80):
    if district_set is None:
        print("No district set provided, use all districts.")
        district_set = DISTRICTS_SET.copy()
        district_set.update(DISTRICTS_SET_NORMALIZED)
    
    part_normalized_string = normalize_string(part)
    part_normalized_vietnamese = normalize_vietnamese(part)
    
    result = process.extractOne(
        part_normalized_string,
        list(district_set),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print("Found district with accent:", matched_key, "Score:", score)
        return matched_key
    
    result = process.extractOne(
        part_normalized_vietnamese,
        list(district_set),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print("Found district with unaccent:", matched_key, "Score:", score)
        return matched_key
    
    return None

def has_district_prefix(part):
    return bool(DISTRICT_PREFIX_REGEX.search(part))


def has_ward_prefix(part):
    return bool(WARD_PREFIX_REGEX.search(part))


def has_province_prefix(part):
    return bool(PROVINCE_PREFIX_REGEX.search(part))


def find_ctryname(part):
    if has_province_prefix(part):
        return part

    return fuzzy_search_province(part)

def _normalize_result(parsed_result: dict) -> dict:
    # Replace non-alphabetic and non-numeric characters with space, but keep spaces
    normalized_result = {}
    for k, v in parsed_result.items():
        if isinstance(v, list):
            normalized_result[k] = [normalize_string(str(item)) for item in v]
        else:
            normalized_result[k] = normalize_string(str(v))

    return normalized_result


def _parse_address(address: str, force=False) -> dict:
    result = {
        "ctryname": "",
        "ctrysubdivname": "",
        "ctrysubsubdivname": [],
    }

    parts = re.split(r"\s*[,;]\s*", address)
    parts = [p for p in parts if p.strip()]

    parts = parts[::-1]

    last_parsed = None    
    
    ward_set = None
    district_set = None
    
    for part in parts:
        if not part:
            continue

        lowered = part.lower()

        if not result["ctryname"]:
            if force:
                result["ctryname"] = lowered
                last_parsed = "ctryname"
            else:
                found = find_ctryname(lowered)
                if found:
                    result["ctryname"] = found
                    last_parsed = "ctryname"
            
            if result["ctryname"]:
                old_province_matched = process.extractBests(
                    result["ctryname"],
                    VN_PROVINCE_DISTRICT_DICT.keys(),
                    scorer=fuzz.partial_ratio,
                    score_cutoff=50,
                    limit=5,
                )
                if old_province_matched:
                    district_set = set()
                    for province in old_province_matched:
                        district_set.update(VN_PROVINCE_DISTRICT_DICT[province[0]])
                
                new_province_matched = process.extractBests(
                    result["ctryname"],
                    VN_PROVINCE_WARD_DICT.keys(),
                    scorer=fuzz.partial_ratio,
                    score_cutoff=50,
                    limit=5,
                )
                if new_province_matched:
                    ward_set = set()
                    for province in new_province_matched:
                        ward_set.update(VN_PROVINCE_WARD_DICT[province[0]])
            
            continue
        
        if has_ward_prefix(lowered):
            if not result["ctrysubsubdivname"]:
                result["ctrysubsubdivname"] = [lowered]
                last_parsed = "ctrysubsubdivname"
                continue
        
        if has_district_prefix(lowered):
            if not result["ctrysubdivname"]:
                result["ctrysubdivname"] = [lowered]
                last_parsed = "ctrysubdivname"
                continue
        
        if not result["ctrysubsubdivname"]:                
            if last_parsed == "ctrysubdivname":
                result["ctrysubsubdivname"] = [lowered]

            found = fuzzy_search_ward(lowered, ward_set)
            if found:
                result["ctrysubsubdivname"] = [lowered]
                last_parsed = "ctrysubsubdivname"
        
        if not result["ctrysubdivname"]:
            if last_parsed == "ctrysubsubdivname":
                # Detected as new address, pass this
                continue
            
            found = fuzzy_search_district(lowered, district_set)
            if found:
                result["ctrysubdivname"] = [found]
                last_parsed = "ctrysubdivname"

    return _normalize_result(result)


def handle_dup_substr(str):
    try:
        for i in range(len(str) // 2, -1, -1):
            idx = str[i:].find(str[:i])
            if idx != -1 and idx < 5 and str[i] == ",":
                return str[i + idx :]
        return str
    except IndexError:
        return str


def remove_redunts(str):
    str_list = [x for x in str.split(",") if x.strip() != ""]
    res = ""
    for sub_str in str_list:
        res += sub_str + ","
    return res[:-1].strip()


def parse_address(address: str) -> dict:
    address = normalize_string(address)
    address = re.sub(
        r"\b(việt nam|vietnam|vn)\b", "", address, flags=re.IGNORECASE
    ).strip()
    address = remove_redunts(handle_dup_substr(address.replace(".", "")))
    address = handle_dash(address)

    parsed_result = _parse_address(address)
    if parsed_result["ctryname"]:
        return parsed_result

    return _parse_address(address, force=True)

