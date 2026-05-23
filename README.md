# HACD IV Score

This folder defines a custom rarity system for HACD: IV Score (Intrinsic Value Score). The core idea is that most traits should have a clear probability, and that any collector-preference curve should be explicitly anchored to a statistical rarity point.

## Sources and Ideas Used

- `https://github.com/hacash/fullnode`
- `https://hacd.fun/`
- `https://hacd.it/`
- `https://hacash.diamonds/`

## Formula

Each CSV row is an event:

```text
probability = occurrences / total_space
score_bits_x100 = round(log2(1 / probability) * 100)
```

Examples:

- `1/16` -> `400` points, because it represents 4 bits of surprise.
- `1/256` -> `800` points.
- `1/4096` -> `1200` points.
- `1/1,048,576` -> `2000` points.

This score scales well because the score doubles whenever rarity is multiplied by powers of two. For a final ranking, it is best to add only traits from independent groups and, within the same `exclusive_group`, keep only the rarest or highest-preference trait that applies. For example, if a name has 6 equal letters, it should not also add the 2-, 3-, 4-, and 5-equal-letter traits.

## Catalog

Generate the CSV with:

```powershell
python .\IVScore\generate_catalog.py
```

Output:

- `hacd_score_catalog.csv`: feature table with probabilities, odds, and score.

Evaluate a specific HACD with:

```powershell
python .\IVScore\score_hacd.py --name WTYUIA --number 123456 --life-gene <64_hex_chars>
```

You can pass only `--name`, only `--number`, or combine all three inputs. The evaluator adds the rarest trait from each `exclusive_group` to avoid hierarchical double counting.
It also avoids the most obvious visual double count: if all 16 facets are a single color, it does not additionally add the matching-bottom-color trait.

Main columns:

- `feature_id`: stable identifier for code use.
- `dimension`: `name`, `visual_shape`, `visual_color`, or `number`.
- `condition`: evaluable rule.
- `total_space` and `occurrences`: mathematical basis of the calculation.
- `probability`: rarity as probability.
- `odds_1_in`: "1 in N" style reading.
- `score_bits_x100`: recommended IV Score.
- `exclusive_group`: family where only the rarest matching trait should be selected.

## Included Criteria

Name:

- Consecutive runs: 2, 3, 4, 5, or 6 equal letters in a row.
- Global repetition: one letter appears 2, 3, 4, 5, or 6 times.
- Explicit symbolic patterns: `XXXYYY`, `XYZXYZ`, `XXYYZZ`, `XYYXYY`, `XXYXXY`, `XYYZZZ`, `XXXYYZ`, `XYYYYX`, `XXYYXX`, `XXXXXX`, `XYZZYX`.

Global letter repetition is scored by probability: `2+ = 61`, `3+ = 389`, `4+ = 824`, `5+ = 1349`, and `6 = 2000`. Names with all distinct letters do not receive this repetition bonus.
For symbolic patterns, repeated symbols must use the same HACD letter and different symbols must use different HACD letters. The resulting pattern scores are probability-based: one-symbol patterns such as `XXXXXX` score `2000`, two-symbol patterns such as `XXXYYY` score `1609`, and three-symbol patterns such as `XYZXYZ` score `1229`.

HIP-5 Visual:

- Non-diamond shape and each individual rare shape.
- Common diamond.
- In the common diamond: lower-facet styles from `hacash.diamonds`: `Pure`, `Edge color`, `Left three pure`, `Left mix pure`, `Right three pure`, `Right mix pure`, `Symmetry`, `Half divide`, `Double mix`, and `Center color`.
- In non-diamond shapes: exact number of facets, from 1 to 15, that match the center color.
- `HIP-5: Color Spectrum` in any shape: exactly 1 through 16 distinct colors across the 16 main HIP-5 slots. The row detail is shown as `HIP-5: N colors`.

Common-diamond lower styles are scored as symbolic patterns from visual left to right on `[color_slot[14], color_slot[12], color_slot[13], color_slot[15]]`: `Pure = AAAA`, `Left three pure = AAAB`, `Left mix pure = AABA`, `Right three pure = BAAA`, `Right mix pure = ABAA`, `Symmetry = ABBA`, `Half divide = AABB`, `Double mix = ABAB`, and `Center color = BAAC`. HIP-5 Color Spectrum is scored statistically with the event `unique_count(color_slot[0:16]) == N`: `1 color = 6000`, `2 colors = 4109`, `3 colors = 2952`, `4 colors = 2123`, `5 colors = 1497`, `6 colors = 1019`, `7 colors = 661`, `8 colors = 405`, `9 colors = 244`, `10 colors = 171`, `11 colors = 187`, `12 colors = 294`, `13 colors = 500`, `14 colors = 819`, `15 colors = 1284`, and `16 colors = 1975`. Extra points for specific diamond zones remain limited to the common diamond; for special shapes, the statistical rule based on how many facets share the center color is preserved.

HACD Number:

- Number with a single repeated digit.
- Palindrome number.
- Ascending or descending serial number.
- Tail of 4, 5, 6, or 7 equal digits.

## Design Notes

The name and part of the HIP-5 colors are not fully independent dimensions: the first 6 color slots of `visual_gene` come from the name. For that reason, the CSV separates groups and provides `exclusive_group` so a final calculator can avoid excessive double counting.

The categories on `hacd.fun` mix mathematical rarity with collector taste. This proposal starts from verifiable probability and leaves market preferences as a later layer: for example, a manual multiplier could be applied to `heart`, `gold`, meaningful words, or collection sets.
