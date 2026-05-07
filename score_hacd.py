#!/usr/bin/env python3
"""Score one HACD against hacd_score_catalog.csv."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


ALPHABET = "WTYUIAHXVMEKBSZN"
SPECIAL_NAME_PATTERNS = (
    "XXXYYY",
    "XYZXYZ",
    "XXYYZZ",
    "XYYXYY",
    "XXYXXY",
    "XYYZZZ",
    "XXXYYZ",
    "XYYYYX",
    "XXYYXX",
    "XXXXXX",
    "XYZZYX",
)
COMMON_BOTTOM_STYLE_PATTERNS = (
    ("hip5_common_bottom_left_three_pure", "AAAB"),
    ("hip5_common_bottom_left_mix_pure", "AABA"),
    ("hip5_common_bottom_right_three_pure", "BAAA"),
    ("hip5_common_bottom_right_mix_pure", "ABAA"),
    ("hip5_common_bottom_symmetry", "ABBA"),
    ("hip5_common_bottom_half_divide", "AABB"),
    ("hip5_common_bottom_double_mix", "ABAB"),
    ("hip5_common_bottom_center_color", "BAAC"),
)
SHAPE_BY_BYTE = {
    1: "square",
    2: "ellipse",
    3: "heart",
    4: "triangle",
    5: "teardrop",
    6: "circle",
    7: "rhombus",
    8: "hexagon",
}


def load_catalog() -> dict[str, dict[str, str]]:
    path = Path(__file__).with_name("hacd_score_catalog.csv")
    if not path.exists():
        raise SystemExit("Missing hacd_score_catalog.csv. Run: python .\\IVScore\\generate_catalog.py")
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["feature_id"]: row for row in csv.DictReader(handle)}


def normalize_name(value: str | None) -> str | None:
    if value is None:
        return None
    name = value.strip().upper()
    if len(name) != 6 or any(char not in ALPHABET for char in name):
        raise SystemExit(f"Invalid HACD name: {value!r}")
    return name


def normalize_life_gene(value: str | None) -> str | None:
    if value is None:
        return None
    gene = value.strip().lower()
    if len(gene) != 64 or any(char not in "0123456789abcdef" for char in gene):
        raise SystemExit("life_gene must be 64 hexadecimal characters")
    return gene


def add(matches: set[str], feature_id: str) -> None:
    matches.add(feature_id)


def name_pattern_id(pattern: str) -> str:
    return f"name_pattern_{pattern.lower()}"


def matches_symbol_pattern(name: str, pattern: str) -> bool:
    mapped: dict[str, str] = {}
    used: set[str] = set()
    for char, symbol in zip(name, pattern, strict=True):
        current = mapped.get(symbol)
        if current is not None:
            if current != char:
                return False
            continue
        if char in used:
            return False
        mapped[symbol] = char
        used.add(char)
    return True


def matches_slot_pattern(slots: list[int], pattern: str) -> bool:
    mapped: dict[str, int] = {}
    used: set[int] = set()
    for slot, symbol in zip(slots, pattern, strict=True):
        current = mapped.get(symbol)
        if current is not None:
            if current != slot:
                return False
            continue
        if slot in used:
            return False
        mapped[symbol] = slot
        used.add(slot)
    return True


def match_name(name: str, matches: set[str]) -> None:
    counts = Counter(name)
    max_count = max(counts.values())

    max_run = 1
    run = 1
    for index in range(1, len(name)):
        if name[index] == name[index - 1]:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1

    for length in range(2, 7):
        if max_run >= length:
            add(matches, f"name_run_ge_{length}")
        if max_count >= length:
            add(matches, f"name_letter_count_ge_{length}")

    for pattern in SPECIAL_NAME_PATTERNS:
        if matches_symbol_pattern(name, pattern):
            add(matches, name_pattern_id(pattern))


def match_number(number: int, matches: set[str]) -> None:
    if number < 1 or number > 16_777_216:
        raise SystemExit("number must be in 1..16777216")
    text = str(number)
    digits = [int(digit) for digit in text]

    if len(set(text)) == 1:
        add(matches, "number_repdigit")
    if text == text[::-1]:
        add(matches, "number_palindrome")
    if len(text) >= 3 and all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1)):
        add(matches, "number_serial_ascending")
    if len(text) >= 3 and all(digits[i] - 1 == digits[i + 1] for i in range(len(digits) - 1)):
        add(matches, "number_serial_descending")
    for length in range(4, 8):
        if len(text) >= length and len(set(text[-length:])) == 1:
            add(matches, f"number_tail_{length}_same_digit")


def visual_color_slots(name: str, life_gene: str) -> list[int]:
    slots = [ALPHABET.index(char) for char in name]
    slots.extend(int(life_gene[index : index + 2], 16) % 16 for index in range(40, 62, 2))
    return slots


def match_visual(name: str | None, life_gene: str, matches: set[str]) -> None:
    shape_byte = int(life_gene[62:64], 16)
    shape = SHAPE_BY_BYTE.get(shape_byte)
    if shape:
        add(matches, "hip5_shape_any_rare")
        add(matches, f"hip5_shape_{shape}")
    else:
        add(matches, "hip5_shape_common")
    if not name:
        return

    slots = visual_color_slots(name, life_gene)
    max_color_count = max(Counter(slots[:16]).values())
    for count in range(2, 17):
        if max_color_count >= count:
            add(matches, f"hip5_all_shapes_same_color_count_ge_{count}")

    if shape:
        center_matches = sum(1 for slot in slots[1:16] if slot == slots[0])
        if center_matches > 0:
            add(matches, f"hip5_special_shape_center_matches_exact_{center_matches}")

    if shape or max_color_count == 16:
        return
    bottom_slots = [slots[14], slots[12], slots[13], slots[15]]
    for feature_id, pattern in COMMON_BOTTOM_STYLE_PATTERNS:
        if matches_slot_pattern(bottom_slots, pattern):
            add(matches, feature_id)
    if slots[14] == slots[15]:
        add(matches, "hip5_common_bottom_corners_same")
    if slots[12] == slots[13] == slots[14] == slots[15]:
        add(matches, "hip5_common_bottom_four_same")


def selected_score(matches: set[str], catalog: dict[str, dict[str, str]]) -> tuple[int, list[dict[str, str]]]:
    by_group: dict[str, dict[str, str]] = {}
    for feature_id in matches:
        row = catalog.get(feature_id)
        if not row:
            continue
        group = row["exclusive_group"] or row["feature_id"]
        current = by_group.get(group)
        if current is None or int(row["score_bits_x100"]) > int(current["score_bits_x100"]):
            by_group[group] = row
    selected = sorted(by_group.values(), key=lambda row: int(row["score_bits_x100"]), reverse=True)
    return sum(int(row["score_bits_x100"]) for row in selected), selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Score one HACD from name, life_gene and/or number.")
    parser.add_argument("--name", help="Six-letter HACD name, e.g. WTYUIA")
    parser.add_argument("--life-gene", help="64 hex characters")
    parser.add_argument("--number", type=int, help="HACD mint number")
    args = parser.parse_args()

    catalog = load_catalog()
    name = normalize_name(args.name)
    life_gene = normalize_life_gene(args.life_gene)
    matches: set[str] = set()

    if name:
        match_name(name, matches)
    if args.number is not None:
        match_number(args.number, matches)
    if life_gene:
        match_visual(name, life_gene, matches)

    total, selected = selected_score(matches, catalog)
    print(f"score_bits_x100={total}")
    for row in selected:
        print(f"{row['score_bits_x100']:>5}  {row['feature_id']}  {row['label']}  odds=1/{row['odds_1_in']}")


if __name__ == "__main__":
    main()
