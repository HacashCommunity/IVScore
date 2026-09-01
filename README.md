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

- Letter composition, ignoring order: `Six matching letters`, `Five matching letters`, `4+2 matching letters`, `3+3 matching letters`, `2+2+2 matching letters`, `Four matching letters`, `3+2 matching letters`, `Three matching letters`, `2+2 matching letters`, `Two matching letters`, and `All letters different`.
- Consecutive matching letters: exact repeated blocks such as `2`, `3`, `2+2`, `3+2`, `2+2+2`, `3+3`, `4+2`, and `6`.
- Explicit symbolic patterns: `ABABAB`, `ABCABC`, and six-letter palindromes.

Letter composition is scored by exact probability: `6 = 2000`, `5+1 = 1351`, `4+2 = 1219`, `3+3 = 1277`, `2+2+2 = 838`, `4+1+1 = 838`, `3+2+1 = 638`, `3+1+1+1 = 426`, `2+2+1+1 = 309`, `2+1+1+1+1 = 109`, and `1+1+1+1+1+1 = 154`.
Consecutive matching letters are also scored by exact repeated-block probability: `2 = 205`, `3 = 628`, `2+2 = 569`, `4 = 1060`, `3+2 = 960`, `5 = 1509`, `2+2+2 = 1219`, `3+3 = 1609`, `4+2 = 1509`, and `6 = 2000`.
For symbolic patterns, repeated symbols must use the same HACD letter and different symbols must use different HACD letters. `ABABAB` scores `1609`, `ABCABC` scores `1229`, and palindromes score `1200`.

HIP-5 Visual:

- Non-diamond shape and each individual rare shape.
- Common diamond.
- In the common diamond: lower-facet styles from `hacash.diamonds`: `Pure`, `Edge color`, `Left three pure`, `Left mix pure`, `Right three pure`, `Right mix pure`, `Symmetry`, `Half divide`, `Double mix`, and `Center color`.
- In non-diamond shapes: exact number of rendered facets that match the center color. Details are shown as `HIP-5: XXXX shape: N facets match center`.
- In the heart shape: exact number of mirror facet pairs that match, using pairs `1-2`, `3-4`, `5-6`, `7-8`, `9-10`, `11-12`, `13-14`, and `15-16`. Details are shown as `HIP-5: Heart shape: N mirror pairs`.
- In the square shape: exact number of mirror facet pairs that match, using pairs `1-4`, `2-3`, `5-6`, `7-8`, `9-10`, `11-12`, `13-16`, and `14-15`. Details are shown as `HIP-5: Square shape: N mirror pairs`.
- In the ellipse shape: exact number of mirror facet pairs that match, using pairs `1-2`, `3-4`, `5-6`, `7-8`, `9-11`, `10-12`, `13-15`, and `14-16`. Details are shown as `HIP-5: Ellipse shape: N mirror pairs`.
- In the teardrop shape: exact number of mirror facet pairs that match, using pairs `1-2`, `3-5`, `4-6`, `7-12`, `8-13`, `9-14`, `10-15`, and `11-16`. Details are shown as `HIP-5: Teardrop shape: N mirror pairs`.
- In the circle shape: exact number of mirror facet pairs that match, using pairs `1-2`, `3-4`, `5-7`, `6-8`, `9-12`, `10-11`, `13-16`, and `14-15`. Details are shown as `HIP-5: Circle shape: N mirror pairs`.
- In the triangle shape: exact number of mirror facet groups that match, using groups `1-2-3`, `4-5`, `6-9`, `7-8`, `10-13`, `11-12`, and `14-15`. Details are shown as `HIP-5: Triangle shape: N mirror groups`.
- In the rhombus shape: exact number of mirror facet pairs that match, using pairs `1-4`, `2-3`, `5-6`, `7-8`, `9-16`, `10-15`, `11-14`, and `12-13`. Details are shown as `HIP-5: Rhombus shape: N mirror pairs`.
- In the hexagon shape: exact number of mirror facet pairs that match, using pairs `1-3`, `2-4`, `5-6`, `7-10`, `8-9`, `11-14`, `12-16`, and `13-15`. Details are shown as `HIP-5: Hexagon shape: N mirror pairs`.
- `HIP-5: Color Spectrum`: exactly 1 through 16 distinct colors across the rendered HIP-5 facets. Common diamond details are shown as `HIP-5: N colors`; special-shape details are shown as `HIP-5: XXXX shape: N colors`.
- `HIP-5: Dark Color`: every rendered facet uses a color index from `0` through `4`.
- `HIP-5: Light Color`: every rendered facet uses a color index from `5` through `15`.

Common-diamond lower styles are scored as symbolic patterns from visual left to right on `[color_slot[14], color_slot[12], color_slot[13], color_slot[15]]`: `Pure = AAAA`, `Left three pure = AAAB`, `Left mix pure = AABA`, `Right three pure = BAAA`, `Right mix pure = ABAA`, `Symmetry = ABBA`, `Half divide = AABB`, `Double mix = ABAB`, and `Center color = BAAC`. HIP-5 Color Spectrum is scored statistically with the event `unique_count(rendered_color_slots) == N`: `1 color = 6000`, `2 colors = 4109`, `3 colors = 2952`, `4 colors = 2123`, `5 colors = 1497`, `6 colors = 1019`, `7 colors = 661`, `8 colors = 405`, `9 colors = 244`, `10 colors = 171`, `11 colors = 187`, `12 colors = 294`, `13 colors = 500`, `14 colors = 819`, `15 colors = 1284`, and `16 colors = 1975` for 16-facet shapes. Extra points for specific diamond zones remain limited to the common diamond; for special shapes, the statistical rule based on how many facets share the center color is preserved. Most special shapes use 17 rendered facets; triangle keeps 16.

Dark/Light Color is an additional statistical group. For 16-facet shapes, all-dark has probability `(5/16)^16` and scores `2685`, while all-light has probability `(11/16)^16` and scores `865`. For 17-facet shapes, the corresponding scores are `2853` and `919`. Mixed dark/light facets receive neither trait.

HACD Number:

- Number with a single repeated digit.
- Palindrome number.
- Ascending or descending serial number.
- Tail of 4, 5, 6, or 7 equal digits.

## Design Notes

The name and part of the HIP-5 colors are not fully independent dimensions: the first 6 color slots of `visual_gene` come from the name. For that reason, the CSV separates groups and provides `exclusive_group` so a final calculator can avoid excessive double counting.

The categories on `hacd.fun` mix mathematical rarity with collector taste. This proposal starts from verifiable probability and leaves market preferences as a later layer: for example, a manual multiplier could be applied to `heart`, `gold`, meaningful words, or collection sets.
