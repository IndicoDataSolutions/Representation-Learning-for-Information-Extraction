import re
from commonregex import CommonRegex
from dateparser.search import search_dates
import spacy


def _search_addresses(all_text):
    parser = CommonRegex(all_text)
    return parser.street_addresses


def _search_names(all_text):
    nlp = spacy.load("en_core_web_lg")
    # raw = nlp(all_text)["ents"]
    raw = nlp(all_text).ents
    filtered = [t for t in raw if t.label_ in ["PERSON", "ORG"]]
    return filtered


def get_invoice_nums(ocr_data):
    inv_nums = []
    invoice_no_re = r"^[0-9a-zA-Z-:]+$"

    all_words = [
        {
            "text": ocr_data["text"][idx],
            "left": ocr_data["left"][idx],
            "top": ocr_data["top"][idx],
            "width": ocr_data["width"][idx],
            "height": ocr_data["height"][idx],
        }
        for idx, word in enumerate(ocr_data["text"])
        if word.strip() != ""
    ]
    for word in all_words:
        if not re.search("\d", word["text"]):
            continue
        if len(word["text"]) < 3:
            continue
        result = re.findall(invoice_no_re, word["text"])
        if result:
            inv_nums.append(
                {
                    "text": word["text"],
                    "x1": word["left"],
                    "y1": word["top"],
                    "x2": word["left"] + word["width"],
                    "y2": word["top"] + word["height"],
                }
            )

    return inv_nums


def _search_blocks(ocr_data):
    # TODD: rewrite this for readapi.
    if "blocks" in ocr_data.keys():
        return [b["text"] for b in ocr_data["blocks"]]

    block_texts = []
    for b in ocr_data["block_num"]:
        block_text = [
            t for b_n, t in zip(ocr_data["block_num"], ocr_data["text"]) if b_n == b
        ]
        block_texts.append(" ".join(block_text))
    return list(set(block_texts))


def get_entities(ocr_data, entity_type="date"):
    entities, all_entities = [], []
    indices = []
    method_dict = {
        "date": search_dates,
        "name": _search_names,
        "address": _search_addresses,
        "block": _search_blocks,
    }

    all_words = [
        {
            "text": ocr_data["text"][idx],
            "left": ocr_data["left"][idx],
            "top": ocr_data["top"][idx],
            "width": ocr_data["width"][idx],
            "height": ocr_data["height"][idx],
        }
        for idx, word in enumerate(ocr_data["text"])
        if word.strip() != ""
    ]

    all_text = " ".join([word["text"].strip() for word in all_words])
    matches = method_dict[entity_type](all_text)

    for match in matches:
        text = match[0]

        token_length = len(text.split(" "))
        idx = all_text.find(match[0])
        text_len = len(text)
        index = len(all_text[:idx].strip().split(" "))

        replaced_text = " ".join(["*" * len(i) for i in text.split(" ")])

        indices.append(list(range(index, index + token_length)))

        index += token_length
        all_text = (
            all_text[: idx + text_len].replace(text, replaced_text)
            + all_text[idx + text_len :]
        )

    for date_indices in indices:
        date = ""
        left, top, right, bottom = [], [], [], []
        for i in date_indices:
            date += " " + all_words[i]["text"]
            left.append(all_words[i]["left"])
            top.append(all_words[i]["top"])
            right.append(all_words[i]["left"] + all_words[i]["width"])
            bottom.append(all_words[i]["top"] + all_words[i]["height"])
        all_entities.append(
            {
                "text": date.strip(),
                "x1": min(left),
                "y1": min(top),
                "x2": max(right),
                "y2": max(bottom),
            }
        )

    return all_entities


def get_amounts(ocr_data):
    amounts = []
    amount_re = r"\$?([0-9]*,)*[0-9]{3,}(\.[0-9]+)?"

    all_words = [
        {
            "text": ocr_data["text"][idx],
            "left": ocr_data["left"][idx],
            "top": ocr_data["top"][idx],
            "width": ocr_data["width"][idx],
            "height": ocr_data["height"][idx],
        }
        for idx, word in enumerate(ocr_data["text"])
        if word.strip() != ""
    ]
    for word in all_words:
        if not re.search(amount_re, word["text"]):
            continue
        try:
            formatted_word = re.sub(r"[$,]", "", word["text"])
            float(formatted_word)

            amounts.append(
                {
                    "text": word["text"],
                    "x1": word["left"],
                    "y1": word["top"],
                    "x2": word["left"] + word["width"],
                    "y2": word["top"] + word["height"],
                }
            )

        except ValueError:
            continue

    return amounts


# data is the full ocr result
def get_candidates(data):
    try:
        date_candidates = get_entities(data, "date")
    except Exception as e:
        date_candidates = []
    try:
        total_amount_candidates = get_amounts(data)
    except Exception as e:
        total_amount_candidates = []
    try:
        numerical_candidates = get_invoice_nums(data)
    except Exception as e:
        numerical_candidates = []
    try:
        name_candidates = get_entities(data, "name")
    except Exception as e:
        name_candidates = []
    try:
        address_candidates = get_entities(data, "address")
    except Exception as e:
        address_candidates = []
    try:
        block_candidates = get_entities(data, "block")
    except Exception as e:
        block_candidates = []

    candidate_data = {
        "Document Title": block_candidates,
        "Document Number": numerical_candidates,
        "Return to Address": address_candidates,
        "Dated Date": date_candidates,
        "Recording Date": date_candidates,
        "Recording Fee": total_amount_candidates,
        "Debtors Name": name_candidates,
        "Debtors Address": address_candidates,
        "Notary Name": name_candidates,
        "Lien Amount": total_amount_candidates,
        "Recording Book": numerical_candidates,
        "Recording Page": numerical_candidates,
        "Claimant Name": name_candidates,
        "Claimant Address": address_candidates,
        "Legal Description": block_candidates,
    }
    return candidate_data
