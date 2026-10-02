import requests
import time
import pandas as pd
from sqlalchemy import text
from database import engine

# Get unique TCGA patient IDs from existing miRNA samples
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT DISTINCT
            split_part(sample_id, '-', 1) || '-' ||
            split_part(sample_id, '-', 2) || '-' ||
            split_part(sample_id, '-', 3) AS patient_id
        FROM mirna_expression
        ORDER BY patient_id
    """))
    patient_ids = [row[0] for row in rows]

print(f"Found {len(patient_ids)} unique TCGA patients.")

url = "https://api.gdc.cancer.gov/cases"
records = []

for i, patient_id in enumerate(patient_ids, 1):
    try:
        query = {
            "filters": {
                "op": "=",
                "content": {
                    "field": "submitter_id",
                    "value": patient_id
                }
            },
            "expand": "demographic,diagnoses",
            "format": "JSON"
        }

        for attempt in range(3):
            try:
                response = requests.post(url, json=query, timeout=60)
                response.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == 2:
                    raise
                print(f"Retry {attempt + 1}/3 for {patient_id}: {e}")
                time.sleep(3)

        hits = response.json()["data"]["hits"]

        if not hits:
            print(f"[{i}/{len(patient_ids)}] No record: {patient_id}")
            continue

        case = hits[0]
        demographic = case.get("demographic") or {}
        diagnosis = (case.get("diagnoses") or [{}])[0]

        records.append({
            "patient_id": patient_id,
            "sex": demographic.get("sex_at_birth"),
            "age_at_index": demographic.get("age_at_index"),
            "race": demographic.get("race"),
            "ethnicity": demographic.get("ethnicity"),
            "vital_status": demographic.get("vital_status"),
            "country_of_residence": demographic.get(
                "country_of_residence_at_enrollment"
            ),
            "primary_site": case.get("primary_site"),
            "disease_type": case.get("disease_type"),
            "primary_diagnosis": diagnosis.get("primary_diagnosis"),
            "tissue_or_organ_of_origin": diagnosis.get(
                "tissue_or_organ_of_origin"
            ),
            "laterality": diagnosis.get("laterality"),
            "tumor_grade": diagnosis.get("tumor_grade"),
            "ajcc_pathologic_stage": diagnosis.get(
                "ajcc_pathologic_stage"
            ),
            "ajcc_pathologic_t": diagnosis.get("ajcc_pathologic_t"),
            "ajcc_pathologic_n": diagnosis.get("ajcc_pathologic_n"),
            "ajcc_pathologic_m": diagnosis.get("ajcc_pathologic_m"),
            "metastasis_at_diagnosis": diagnosis.get(
                "metastasis_at_diagnosis"
            ),
            "prior_malignancy": diagnosis.get("prior_malignancy"),
            "prior_treatment": diagnosis.get("prior_treatment"),
            "method_of_diagnosis": diagnosis.get("method_of_diagnosis"),
            "year_of_diagnosis": diagnosis.get("year_of_diagnosis"),
            "progression_or_recurrence": diagnosis.get(
                "progression_or_recurrence"
            ),
            "days_to_last_follow_up": diagnosis.get(
                "days_to_last_follow_up"
            ),
            "days_to_recurrence": diagnosis.get("days_to_recurrence"),
            "last_known_disease_status": diagnosis.get(
                "last_known_disease_status"
            ),
        })

        if i % 50 == 0:
            print(f"Processed {i}/{len(patient_ids)} patients.")

    except Exception as e:
        print(f"[{i}/{len(patient_ids)}] ERROR {patient_id}: {e}")

df = pd.DataFrame(records)

output_file = "data/tcga_brca_patient_clinical.csv"
df.to_csv(output_file, index=False)

print(f"\nSaved {len(df)} patient records to {output_file}")
print(f"Columns: {len(df.columns)}")
