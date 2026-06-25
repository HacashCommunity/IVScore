#!/usr/bin/env python3
"""
Generate a HACD rarity feature catalog.

The catalog is intentionally probability-first: every row defines an event,
its sample space, its occurrence count, and a score derived from surprise bits.
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, getcontext
from itertools import product
from pathlib import Path


ALPHABET = "WTYUIAHXVMEKBSZN"
NAME_SPACE = len(ALPHABET) ** 6
MAX_HACD = 16_777_216
NAME_COMPOSITION_PATTERNS = (
    ("name_letter_count_6", "Six matching letters", (6,)),
    ("name_letter_count_5_1", "Five matching letters", (5, 1)),
    ("name_letter_count_4_2", "4+2 matching letters", (4, 2)),
    ("name_letter_count_3_3", "3+3 matching letters", (3, 3)),
    ("name_letter_count_2_2_2", "2+2+2 matching letters", (2, 2, 2)),
    ("name_letter_count_4_1_1", "Four matching letters", (4, 1, 1)),
    ("name_letter_count_3_2_1", "3+2 matching letters", (3, 2, 1)),
    ("name_letter_count_3_1_1_1", "Three matching letters", (3, 1, 1, 1)),
    ("name_letter_count_2_2_1_1", "2+2 matching letters", (2, 2, 1, 1)),
    ("name_letter_count_2_1_1_1_1", "Two matching letters", (2, 1, 1, 1, 1)),
    ("name_letter_count_1_1_1_1_1_1", "All letters different", (1, 1, 1, 1, 1, 1)),
)
NAME_CONSECUTIVE_PATTERNS = (
    ("name_consecutive_matching_letters_6", "Six consecutive matching letters", (6,)),
    ("name_consecutive_matching_letters_4_2", "4+2 consecutive matching letters", (4, 2)),
    ("name_consecutive_matching_letters_3_3", "3+3 consecutive matching letters", (3, 3)),
    ("name_consecutive_matching_letters_2_2_2", "2+2+2 consecutive matching letters", (2, 2, 2)),
    ("name_consecutive_matching_letters_5", "Five consecutive matching letters", (5,)),
    ("name_consecutive_matching_letters_3_2", "3+2 consecutive matching letters", (3, 2)),
    ("name_consecutive_matching_letters_4", "Four consecutive matching letters", (4,)),
    ("name_consecutive_matching_letters_2_2", "2+2 consecutive matching letters", (2, 2)),
    ("name_consecutive_matching_letters_3", "Three consecutive matching letters", (3,)),
    ("name_consecutive_matching_letters_2", "Two consecutive matching letters", (2,)),
)
SPECIAL_NAME_PATTERNS = (
    ("name_pattern_ababab", "ABABAB pattern", "ABABAB"),
    ("name_pattern_abcabc", "ABCABC pattern", "ABCABC"),
)
COMMON_BOTTOM_STYLE_PATTERNS = (
    ("hip5_common_bottom_left_three_pure", "Left three pure", "AAAB"),
    ("hip5_common_bottom_left_mix_pure", "Left mix pure", "AABA"),
    ("hip5_common_bottom_right_three_pure", "Right three pure", "BAAA"),
    ("hip5_common_bottom_right_mix_pure", "Right mix pure", "ABAA"),
    ("hip5_common_bottom_symmetry", "Symmetry", "ABBA"),
    ("hip5_common_bottom_half_divide", "Half divide", "AABB"),
    ("hip5_common_bottom_double_mix", "Double mix", "ABAB"),
    ("hip5_common_bottom_center_color", "Center color", "BAAC"),
)

SHAPES = {
    "square": 1,
    "ellipse": 2,
    "heart": 3,
    "triangle": 4,
    "teardrop": 5,
    "circle": 6,
    "rhombus": 7,
    "hexagon": 8,
}

CSV_FIELDS = [
    "feature_id",
    "dimension",
    "label",
    "description",
    "condition",
    "total_space",
    "occurrences",
    "probability",
    "odds_1_in",
    "score_bits_x100",
    "exclusive_group",
    "source",
]

getcontext().prec = 48


@dataclass(frozen=True)
class Feature:
    feature_id: str
    dimension: str
    label: str
    description: str
    condition: str
    total_space: int
    occurrences: int
    exclusive_group: str
    source: str
    score_override: int | None = None

    def to_row(self) -> dict[str, str | int]:
        probability = Decimal(self.occurrences) / Decimal(self.total_space)
        odds = Decimal(self.total_space) / Decimal(self.occurrences)
        score = self.score_override
        if score is None:
            score = round(math.log2(self.total_space / self.occurrences) * 100)
        return {
            "feature_id": self.feature_id,
            "dimension": self.dimension,
            "label": self.label,
            "description": self.description,
            "condition": self.condition,
            "total_space": self.total_space,
            "occurrences": self.occurrences,
            "probability": f"{probability:.18g}",
            "odds_1_in": f"{odds:.12g}",
            "score_bits_x100": score,
            "exclusive_group": self.exclusive_group,
            "source": self.source,
        }


def add(
    rows: list[Feature],
    feature_id: str,
    dimension: str,
    label: str,
    description: str,
    condition: str,
    total_space: int,
    occurrences: int,
    exclusive_group: str,
    source: str,
    score_override: int | None = None,
) -> None:
    if occurrences <= 0 or occurrences > total_space:
        raise ValueError(f"bad occurrence count for {feature_id}: {occurrences}/{total_space}")
    rows.append(
        Feature(
            feature_id,
            dimension,
            label,
            description,
            condition,
            total_space,
            occurrences,
            exclusive_group,
            source,
            score_override,
        )
    )


def permutations(n: int, k: int) -> int:
    value = 1
    for part in range(n - k + 1, n + 1):
        value *= part
    return value


def name_pattern_id(pattern: str) -> str:
    return f"name_pattern_{pattern.lower()}"


def name_pattern_occurrences(pattern: str) -> int:
    return permutations(len(ALPHABET), len(set(pattern)))


def symbol_pattern_occurrences(pattern: str, symbol_space: int = 16) -> int:
    return permutations(symbol_space, len(set(pattern)))


def count_name_patterns() -> Counter[str]:
    counts: Counter[str] = Counter()
    for name in product(range(len(ALPHABET)), repeat=6):
        letter_counts = Counter(name)
        composition = tuple(sorted(letter_counts.values(), reverse=True))

        consecutive: list[int] = []
        run = 1
        for index in range(1, len(name)):
            if name[index] == name[index - 1]:
                run += 1
            else:
                if run >= 2:
                    consecutive.append(run)
                run = 1
        if run >= 2:
            consecutive.append(run)
        if consecutive:
            counts[f"consecutive_{'_'.join(str(item) for item in sorted(consecutive, reverse=True))}"] += 1

        counts[f"composition_{'_'.join(str(item) for item in composition)}"] += 1
        if name == name[::-1]:
            counts["palindrome"] += 1

    return counts


def count_number_patterns() -> Counter[str]:
    counts: Counter[str] = Counter()
    for number in range(1, MAX_HACD + 1):
        text = str(number)
        digits = [int(digit) for digit in text]
        if len(set(text)) == 1:
            counts["number_repdigit"] += 1
        if text == text[::-1]:
            counts["number_palindrome"] += 1
        if len(text) >= 3 and all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1)):
            counts["number_serial_ascending"] += 1
        if len(text) >= 3 and all(digits[i] - 1 == digits[i + 1] for i in range(len(digits) - 1)):
            counts["number_serial_descending"] += 1
        for length in range(4, 8):
            if len(text) >= length and len(set(text[-length:])) == 1:
                counts[f"tail_{length}_same_digit"] += 1
    return counts


def stirling_second_kind(n: int, k: int) -> int:
    table = [[0 for _ in range(k + 1)] for _ in range(n + 1)]
    table[0][0] = 1
    for row in range(1, n + 1):
        for col in range(1, min(row, k) + 1):
            table[row][col] = col * table[row - 1][col] + table[row - 1][col - 1]
    return table[n][k]


def color_distinct_exact_occurrences(count: int) -> int:
    return permutations(16, count) * stirling_second_kind(16, count)


def build_catalog() -> list[Feature]:
    rows: list[Feature] = []
    name_counts = count_name_patterns()
    number_counts = count_number_patterns()

    for feature_id, label, pattern in NAME_CONSECUTIVE_PATTERNS:
        add(
            rows,
            feature_id,
            "name",
            label,
            f"The name contains consecutive matching-letter groups with sizes {'+'.join(str(item) for item in pattern)}.",
            f"consecutive_group_sizes(name) == {pattern}",
            NAME_SPACE,
            name_counts[f"consecutive_{'_'.join(str(item) for item in pattern)}"],
            "name_consecutive_matching_letters",
            "local-combinatorics",
        )

    for feature_id, label, pattern in NAME_COMPOSITION_PATTERNS:
        add(
            rows,
            feature_id,
            "name",
            label,
            f"The name has exact matching-letter composition {'+'.join(str(item) for item in pattern)}, ignoring order.",
            f"letter_count_partition(name) == {pattern}",
            NAME_SPACE,
            name_counts[f"composition_{'_'.join(str(item) for item in pattern)}"],
            "name_letter_count",
            "local-combinatorics",
        )

    for feature_id, label, pattern in SPECIAL_NAME_PATTERNS:
        add(
            rows,
            feature_id,
            "name",
            label,
            f"Symbolic pattern {pattern}; each distinct symbol must map to a distinct HACD letter.",
            f"matches_symbol_pattern(name, '{pattern}')",
            NAME_SPACE,
            name_pattern_occurrences(pattern),
            "name_special_pattern",
            "local-combinatorics",
        )
    add(
        rows,
        "name_pattern_palindrome",
        "name",
        "Palindrome",
        "The HACD name reads the same forward and backward.",
        "name == reverse(name)",
        NAME_SPACE,
        name_counts["palindrome"],
        "name_special_pattern",
        "local-combinatorics",
    )

    add(rows, "hip5_shape_any_rare", "visual_shape", "Non-diamond shape", "Any irregular HIP-5 shape: square, ellipse, heart, triangle, teardrop, circle, rhombus, or hexagon.", "life_gene[31] in 0x01..0x08", 256, 8, "hip5_shape", "fullnode/explorer HIP-5 shape rule")
    add(rows, "hip5_shape_common", "visual_shape", "Common diamond", "Standard HIP-5 diamond shape.", "life_gene[31] not in 0x01..0x08", 256, 248, "hip5_shape", "fullnode/explorer HIP-5 shape rule")
    for shape, item in SHAPES.items():
        add(rows, f"hip5_shape_{shape}", "visual_shape", f"{shape.title()} shape", f"Exact shape byte for {shape}.", f"life_gene[31] == 0x{item:02x}", 256, 1, "hip5_shape", "fullnode/explorer HIP-5 shape rule")

    common_shape_occurrences = 248
    color_space = 16**16
    add(rows, "hip5_common_bottom_corners_same", "visual_color", "Edge color", "In the common diamond, the two lower corner facets use the same color index.", "shape == common and color_slot[14] == color_slot[15]", 256 * 16**2, common_shape_occurrences * 16, "hip5_common_bottom", "hacash.diamonds style + local HIP-5 slot map")
    add(rows, "hip5_common_bottom_four_same", "visual_color", "Pure", "In the common diamond, all four lower facets use the same color index.", "shape == common and color_slot[12] == color_slot[13] == color_slot[14] == color_slot[15]", 256 * 16**4, common_shape_occurrences * 16, "hip5_common_bottom", "hacash.diamonds style + local HIP-5 slot map")
    for feature_id, label, pattern in COMMON_BOTTOM_STYLE_PATTERNS:
        add(
            rows,
            feature_id,
            "visual_color",
            label,
            f"In the common diamond, the four lower facets follow the {pattern} pattern.",
            f"shape == common and matches_symbol_pattern([color_slot[14], color_slot[12], color_slot[13], color_slot[15]], '{pattern}')",
            256 * 16**4,
            common_shape_occurrences * symbol_pattern_occurrences(pattern),
            "hip5_common_bottom",
            "hacash.diamonds style + local HIP-5 slot map",
        )
    for matches in range(1, 16):
        occurrences = 16 * math.comb(15, matches) * (15 ** (15 - matches))
        add(
            rows,
            f"hip5_special_shape_center_matches_exact_{matches}",
            "visual_color",
            f"Special shape with {matches} center-color matching facets",
            f"Conditioned on a non-diamond shape: exactly {matches} of the other 15 main slots match the center slot.",
            f"given shape != common: count(color_slot[1:16] == color_slot[0]) == {matches}",
            color_space,
            occurrences,
            "hip5_special_center_match",
            "local HIP-5 slot map",
        )
    for count in range(1, 17):
        occurrences = color_distinct_exact_occurrences(count)
        add(
            rows,
            f"hip5_color_spectrum_exact_{count}",
            "visual_color",
            "HIP-5: Color Spectrum",
            f"HIP-5: {count} colors. Exactly {count} distinct color indexes appear across the 16 main HIP-5 slots.",
            f"unique_count(color_slot[0:16]) == {count}",
            color_space,
            occurrences,
            "hip5_color_spectrum",
            "local HIP-5 color spectrum occupancy",
        )

    for feature_id, label, key in [
        ("number_repdigit", "Single repeated digit number", "number_repdigit"),
        ("number_palindrome", "Palindrome number", "number_palindrome"),
        ("number_serial_ascending", "Ascending serial number", "number_serial_ascending"),
        ("number_serial_descending", "Descending serial number", "number_serial_descending"),
    ]:
        add(rows, feature_id, "number", label, "Pattern applied to the HACD mint number.", key, MAX_HACD, number_counts[key], "number_literal", "hacd.fun: numberliteral + local-combinatorics")

    for length in range(4, 8):
        add(
            rows,
            f"number_tail_{length}_same_digit",
            "number",
            f"{length}-digit matching tail",
            f"The last {length} digits of the HACD number are equal.",
            f"len(number) >= {length} and unique(last_{length}_digits) == 1",
            MAX_HACD,
            number_counts[f"tail_{length}_same_digit"],
            "number_tail",
            "hacd.fun: numberliteral Tail four/seven + local-combinatorics",
        )

    return rows


def main() -> None:
    out_path = Path(__file__).with_name("hacd_score_catalog.csv")
    rows = build_catalog()
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_row())
    print(f"wrote {out_path} ({len(rows)} features)")


if __name__ == "__main__":
    main()
