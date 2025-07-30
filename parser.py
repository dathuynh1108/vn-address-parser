import re
from fuzzywuzzy import fuzz, process
from utils import normalize_vietnamese, normalize_string, has_number
from data import NEW_ADDRESS, OLD_ADDRESS, SPECIAL_PROVINCE_MAP, DASH_CASES

VN_PROVINCES_SET = set()
for province in OLD_ADDRESS.keys():
    VN_PROVINCES_SET.add(normalize_string(province))

VN_PROVINCES_NORMALIZED_SET = {
    normalize_vietnamese(province) for province in VN_PROVINCES_SET
}

PROVINCE_LOOKUP = VN_PROVINCES_SET
PROVINCE_LOOKUP.update(VN_PROVINCES_NORMALIZED_SET)

# Also create a set of all wards for faster searching
NEW_WARDS = set()
for province, wards in NEW_ADDRESS.items():
    for ward in wards:
        NEW_WARDS.add(normalize_string(ward))

# Alternative: Create normalized versions for better matching
NEW_WARDS_NORMALIZED = {normalize_vietnamese(ward) for ward in NEW_WARDS}

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
        list(SPECIAL_PROVINCE_MAP.keys()),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print(
            "Found province with special case:",
            SPECIAL_PROVINCE_MAP[matched_key],
            "Score:",
            score,
        )
        return SPECIAL_PROVINCE_MAP[matched_key]

    # Find best match, with accentive fuzzy matching
    result = process.extractOne(
        part_normalized_string,
        list(PROVINCE_LOOKUP),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )

    if result:
        matched_key, score = result
        print("Found province with accent set:", matched_key, "Score:", score)
        return matched_key

    result = process.extractOne(
        part_normalized_vietnamese,
        list(PROVINCE_LOOKUP),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print("Found province with unaccent set:", matched_key, "Score:", score)
        return matched_key

    return None

def fuzzy_search_ward(part, fuzzy_threshold=80):
    part_normalized_string = normalize_string(part)
    part_normalized_vietnamese = normalize_vietnamese(part)

    result = process.extractOne(
        part_normalized_string,
        list(NEW_WARDS),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print("Found ward with accent set:", matched_key, "Score:", score)
        return matched_key

    result = process.extractOne(
        part_normalized_vietnamese,
        list(NEW_WARDS_NORMALIZED),
        scorer=fuzz.partial_ratio,
        score_cutoff=fuzzy_threshold,
    )
    if result:
        matched_key, score = result
        print("Found ward with unaccent set:", matched_key, "Score:", score)
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

def find_ctrysubsubdivname(part):
    if has_ward_prefix(part):
        return part

    return fuzzy_search_ward(part)

def is_ctrysubdivname(part):
    return has_district_prefix(part)


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
        else:
            if not result["ctrysubdivname"] and is_ctrysubdivname(lowered):
                result["ctrysubdivname"] = lowered
                last_parsed = "ctrysubdivname"
            
            elif not result["ctrysubsubdivname"]:
                if last_parsed == "ctrysubdivname":
                    result["ctrysubsubdivname"] = [lowered]
                
                found = find_ctrysubsubdivname(lowered)
                if found:
                    result["ctrysubsubdivname"] = [lowered]
                    last_parsed = "ctrysubsubdivname"
            
            else:
                continue

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

