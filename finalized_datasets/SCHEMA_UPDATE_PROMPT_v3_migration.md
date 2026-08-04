# SCHEMA UPDATE PROMPT — Migrate to Dataset v3

**Read this entire document before changing any file. This is a schema MIGRATION, not a rebuild — the goal is to reconcile `feature_schema.json` (and its dependent contracts) with the new v3 datasets, while (1) first accounting for any undocumented schema patches you already made locally during build/testing, and (2) NOT guessing on the items explicitly marked BLOCKED below.**

---

## Step 0 — Report your current actual state FIRST, before changing anything

Before applying any of the changes below: the schema you're currently running may already differ from what Claude last has on record, since you made live fixes during Mapper build/testing that were never reported back. **Before touching any file, produce a short report of:**
- Every field/alias/unit/threshold you changed in `feature_schema.json` since the version Claude originally provided, and why (what error prompted each fix).
- Any field in `contract_1_document_reader.json`, `contract_2_feature_mapper_state.json`, or the Mapper's own code that no longer matches what Claude has on record.

This report should come back to the user before Step 1 begins, so nothing gets silently overwritten or duplicated. **Do not skip this step even if it feels redundant — reconciling drift is the actual point of doing it first.**

---

## Step 1 — Clinical model changes (CONFIRMED, safe to implement)

**1a. Field renames (unit suffix dropped from name):**
| Old field name | New field name |
|---|---|
| `Height_cm` | `Height` |
| `Weight_kg` | `Weight` |
| `Waist_Circumference_cm` | `Waist_Circumference` |
| `LDL_Cholesterol` | `LDL` |
| `HDL_Cholesterol` | `HDL` |

Update the field's `unit` value to stay whatever it already was (cm/kg — the unit itself hasn't changed, only the column NAME dropped the suffix). Update every reference to these field names across `feature_schema.json`, `contract_1`, `contract_2`, `contract_3`, and the Mapper's code (aliases, column_order, any hardcoded field-name strings) — a rename that's applied in the schema but missed in the Mapper's matching code will silently break matching for that field.

**1b. New `column_order` for Clinical (matches the v3 CSV exactly):**
```
Age, Gender, Height, Weight, BMI, Waist_Circumference, Systolic_BP, Diastolic_BP,
Fasting_Blood_Glucose, HbA1c, Triglycerides, HDL, LDL, ALT, AST,
Family_History_Diabetes, Family_History_Hypertension, Family_History_CVD
```
Note the reordering (Triglycerides, HDL, LDL — not the old LDL, HDL, Triglycerides order) and the Family History reduction below.

**1c. Family History fields — reduced from 4 to 3:**
- **REMOVE** `Family_History_Obesity` and `Family_History_NAFLD` from the schema entirely (not in the v3 dataset).
- **ADD** `Family_History_CVD` (new field) — same treatment as the other Family History fields: `type: boolean`, `source: user_form`, Yes/No only (no "unsure"), `encoding: {"Yes": 1, "No": 0}`, direct user-form question text (e.g. "Does a close blood relative have cardiovascular disease?").
- Keep `Family_History_Diabetes` and `Family_History_Hypertension` as they were.

**1d. Gender pre-encoding in the training data — IMPORTANT, do not misapply this:**
The v3 Clinical CSV has `Gender` already stored as `1`/`0` numerically. **This is a training-data convenience only — it does NOT mean real uploaded user reports will say "1" or "0".** A real report will still say "Male"/"Female" as text. Do NOT change the Mapper's Gender-parsing/matching logic to expect a numeric value from extracted report text — the existing `Male=1, Female=0` encoding rule in the schema still applies at the point where a text value gets converted to a number; nothing about the Mapper's extraction logic should change here.

---

## Step 2 — Gut model changes (mostly confirmed, ONE item needs your confirmation)

**2a. CONFIRMED — 10 features added, going from 10 to 20 total:**
New fields to add to the schema (same pattern as existing gut features — `type: float`, `unit: "relative abundance %"`, `valid_range: [0, 30]`, `source: report_extraction`, appropriate `aliases`):
`Bacteroides`, `Ruminococcus`, `Coprococcus`, `Subdoligranulum`, `Enterococcus`, `Eubacterium`, `Parabacteroides`, `Lactobacillus`, `Klebsiella`, `Streptococcus`, `Eggerthella`, `Other_Taxa`

Wait — that's 12 new names for "10 features added." Recount against the actual v3 CSV header before implementing: the full v3 gut column list is `Akkermansia, Faecalibacterium, Roseburia, Bifidobacterium, Bacteroides, Prevotella, Ruminococcus, Blautia, Collinsella, Escherichia_Shigella, Coprococcus, Alistipes, Subdoligranulum, Enterococcus, Eubacterium, Parabacteroides, Lactobacillus, Klebsiella, Streptococcus, Eggerthella, Other_Taxa` — **20 fields total**, use this exact list and exact order for the new `column_order`. Verify count = 20 before finalizing, don't trust my recount above over the actual CSV header.

**2b. CONFIRMED — `Shannon_Diversity_Index` is removed entirely.** Remove it from the schema, from `column_order`, and from any Mapper code/aliases/tests referencing it.

**2c. RESOLVED (Claude's judgment call, not team-confirmed — flag as such in code comments/logs): Age/Gender absence from the Gut file is normalized storage, not feature removal.**
Reasoning: all v3 files still share `Patient_ID`, and labels already moved to a join-by-ID file — this looks like standard normalization (don't duplicate Age/Gender in every export, join from Clinical at training time). **This requires NO change to the Mapper or to Gut's `column_order`** — Age/Gender were already `shared_features`, sourced from whichever report they're found in, not specifically a Gut-model-only field. Keep Age/Gender in Gut's `column_order` exactly as before. If this assumption turns out to be wrong (i.e. the Gut model was actually retrained without Age/Gender), that will surface as a shape mismatch when Contract 3's vector is built — watch for that during first real training/inference test.

---

## Step 3 — Wearable model changes (RESOLVED, Claude's judgment call — implement, but flag as inferred not team-confirmed)

**Resolution: Wearable remains ONE combined model**, now sourced from two files joined on `Patient_ID` (`wearable_standard_v3.csv` + `wearable_cgm_v3.csv`), not two separate models. Reasoning: both share the join key, the original design always combined activity + glucose stats into one model, and a genuine second-model split would be a much larger architecture change (new fusion weight, new XAI handling) than anything else in this refresh suggests — this looks like a practical data-export convenience (not every user has a CGM, but many have a fitness tracker), not a model redesign. **If this turns out wrong, it will surface as a shape mismatch when the real trained model is connected — watch for that.**

**New Wearable `column_order` (15 activity+CGM fields + Age/Gender = 17 total):**
```
Age, Gender,
Average_Daily_Steps, Active_Minutes, Sedentary_Time_Minutes, Resting_Heart_Rate,
Heart_Rate_Variability_RMSSD, Sleep_Duration_Hours, Sleep_Efficiency_Score,
Autonomic_Stress_Score, Activity_Energy_Expenditure, Exercise_Frequency_Days,
CGM_Average_Glucose, CGM_Glucose_CV, CGM_Time_In_Range, CGM_Time_Above_Range, CGM_Time_Below_Range
```

**Field-by-field changes from the old schema:**
| Old field | New field | Notes |
|---|---|---|
| `Average_Daily_Steps` | same | kept |
| `Active_Minutes` | same | kept |
| `Sedentary_Time_Minutes` | same | kept |
| `Resting_Heart_Rate` | same | kept |
| `Sleep_Duration` | `Sleep_Duration_Hours` | renamed |
| `Calories_Burned` | `Activity_Energy_Expenditure` | **treated as a rename** — low-confidence call, verify the value ranges/scale actually match before assuming these are the same underlying measurement, not a genuinely different metric |
| `Average_Glucose` | `CGM_Average_Glucose` | renamed (moved to CGM file) |
| `Glucose_Variability` | `CGM_Glucose_CV` | renamed |
| `Time_In_Range` | `CGM_Time_In_Range` | renamed |
| `Time_Above_Range` | `CGM_Time_Above_Range` | renamed |
| — | `CGM_Time_Below_Range` | new |
| — | `Heart_Rate_Variability_RMSSD` | new |
| — | `Sleep_Efficiency_Score` | new |
| — | `Autonomic_Stress_Score` | new |
| — | `Exercise_Frequency_Days` | new |

Apply the same treatment as Clinical/Gut: update `feature_schema.json` (aliases, units, valid_range for each field — use sensible plausibility ranges for the new fields, e.g. `Sleep_Efficiency_Score` and `Autonomic_Stress_Score` as 0-100), `column_order`, and every Mapper code reference to old field names. Add `wearable_cgm_note` and `wearable_standard_note` to the schema documenting that these two files are joined by `Patient_ID` at training time but represent ONE model's input at inference time — this join detail matters for whoever writes the training script, even though it doesn't change the Mapper's behavior (the Mapper just needs to resolve all 17 fields regardless of which report they came from, same as it always has).

---

## Step 4 — Labels (downstream model-output change, not a schema/Mapper input change)

Reminder: labels are the model's OUTPUT, never part of `feature_schema.json`'s INPUT schema (this has been a hard rule throughout this project — do not add these to the feature schema). However, document this for whoever owns Contract 3/model-output handling downstream:
- Labels moved to a standalone `labels_v3.csv`, joined by `Patient_ID` — no longer embedded per-dataset.
- **`Healthy` label removed** — now presumably implicit (healthy = all 5 other labels are 0). Confirm this assumption with the team before any downstream code relies on it.
- **`Obesity` renamed to `High_Adiposity_Risk`** — flag for the team: confirm whether this is purely a rename or an actual redefinition of the label logic (e.g. now combining BMI + Waist_Circumference rather than BMI alone) — this affects how any prior "Obesity is 100% deterministic from BMI" finding should be reinterpreted.

`split_manifest_v3.csv` (Train/Test/Val assignment) is a training-side concern only — no action needed in the preprocessing unit for this file.

---

## Step 5 — After schema changes: mandatory re-verification

Renaming/reordering/removing fields breaks things silently if not re-checked. Before considering this migration done:
1. Re-run the FULL Mapper test suite. Expect failures on any test that hardcoded an old field name (`Waist_Circumference_cm`, `LDL_Cholesterol`, `HDL_Cholesterol`, `Height_cm`, `Weight_kg`, `Shannon_Diversity_Index`, `Family_History_Obesity`, `Family_History_NAFLD`) — update those test fixtures to match v3 names, don't just delete failing tests.
2. Verify `column_order` for Clinical and Gut against the ACTUAL v3 CSV headers programmatically (not by eye) — this project has caught real column-order bugs this way before (the Gut model's column order was wrong in an earlier round for exactly this reason).
3. Bump `feature_schema.json`'s `schema_version` (e.g. to `2.0.0`, since this includes breaking changes — field removals, not just additions) and add a changelog entry summarizing this migration, explicitly noting which decisions were Claude's inferred judgment calls (Gut/Wearable Age-Gender normalization, Wearable single-model interpretation, Calories_Burned→Activity_Energy_Expenditure treated as rename) pending final team sign-off.
4. Report back final field counts per model: **Clinical: 18 total** (15 features + Age/Gender + note the 3-not-4 Family History fields), **Gut: 22 total** (20 taxa/diversity features + Age/Gender), **Wearable: 17 total** (15 activity+CGM features + Age/Gender).
