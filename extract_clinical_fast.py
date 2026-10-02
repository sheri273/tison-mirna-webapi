import requests
import pandas as pd
import time
from sqlalchemy import text
from database import engine

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT DISTINCT
            split_part(sample_id, '-', 1) || '-' ||
            split_part(sample_id, '-', 2) || '-' ||
            split_part(sample_id, '-', 3) AS patient_id
        FROM mirna_expression
        ORDER BY patient_id
    """)).fetchall()

patient_ids = [r[0] for r in rows]
print(f"Found {len(patient_ids)} unique TCGA patients.")

url = "https://api.gdc.cancer.gov/cases"
records = []
batch_size = 50

for start in range(0, len(patient_ids), batch_size):
    batch = patient_ids[start:start + batch_size]
    batch_no = start // batch_size + 1
    total_batches = (len(patient_ids) + batch_size - 1) // batch_size

    query = {
        "filters": {
            "op": "in",
            "content": {
                "field": "submitter_id",
                "value": batch
            }
        },
        "expand": "demographic,diagnoses,follow_ups",
        "format": "JSON",
        "size": 100
    }

    response = None

    for attempt in range(3):
        try:
            response = requests.post(url, json=query, timeout=120)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            print(f"Batch {batch_no}/{total_batches}: retry {attempt + 1}/3 - {e}")
            time.sleep(5)

    if response is None:
        print(f"Batch {batch_no} FAILED.")
        continue

    hits = response.json()["data"]["hits"]

    for case in hits:
        patient_id = case.get("submitter_id")

        demographic = case.get("demographic") or {}
        diagnoses = case.get("diagnoses") or []
        diagnosis = diagnoses[0] if diagnoses else {}
        followups = case.get("follow_ups") or []

        latest_followup = {}
        if followups:
            latest_followup = max(
                followups,
                key=lambda x: x.get("days_to_follow_up") or -1
            )

        records.append({
            "patient_id": patient_id,

            # Demographics
            "sex": demographic.get("sex_at_birth"),
            "age_at_index": demographic.get("age_at_index"),
            "age_at_diagnosis_days": diagnosis.get("age_at_diagnosis"),
            "race": demographic.get("race"),
            "ethnicity": demographic.get("ethnicity"),
            "country_of_residence": demographic.get("country_of_residence_at_enrollment"),
            "year_of_birth": demographic.get("year_of_birth"),
            "year_of_death": demographic.get("year_of_death"),
            "vital_status": demographic.get("vital_status"),

            # Cancer diagnosis
            "primary_site": case.get("primary_site"),
            "disease_type": case.get("disease_type"),
            "primary_diagnosis": diagnosis.get("primary_diagnosis"),
            "tissue_or_organ_of_origin": diagnosis.get("tissue_or_organ_of_origin"),
            "site_of_resection_or_biopsy": diagnosis.get("site_of_resection_or_biopsy"),
            "laterality": diagnosis.get("laterality"),
            "tumor_grade": diagnosis.get("tumor_grade"),
            "morphology": diagnosis.get("morphology"),
            "icd_10_code": diagnosis.get("icd_10_code"),
            "classification_of_tumor": diagnosis.get("classification_of_tumor"),
            "sites_of_involvement": diagnosis.get("sites_of_involvement"),

            # Staging
            "ajcc_staging_system_edition": diagnosis.get("ajcc_staging_system_edition"),
            "ajcc_pathologic_stage": diagnosis.get("ajcc_pathologic_stage"),
            "ajcc_pathologic_t": diagnosis.get("ajcc_pathologic_t"),
            "ajcc_pathologic_n": diagnosis.get("ajcc_pathologic_n"),
            "ajcc_pathologic_m": diagnosis.get("ajcc_pathologic_m"),
            "metastasis_at_diagnosis": diagnosis.get("metastasis_at_diagnosis"),

            # Disease history
            "synchronous_malignancy": diagnosis.get("synchronous_malignancy"),
            "prior_malignancy": diagnosis.get("prior_malignancy"),
            "prior_treatment": diagnosis.get("prior_treatment"),
            "method_of_diagnosis": diagnosis.get("method_of_diagnosis"),
            "year_of_diagnosis": diagnosis.get("year_of_diagnosis"),
            "progression_or_recurrence": diagnosis.get("progression_or_recurrence"),
            "days_to_recurrence": diagnosis.get("days_to_recurrence"),

            # Follow-up / outcome
            "days_to_diagnosis": diagnosis.get("days_to_diagnosis"),
            "days_to_last_follow_up": diagnosis.get("days_to_last_follow_up"),
            "days_to_last_known_disease_status": diagnosis.get("days_to_last_known_disease_status"),
            "last_known_disease_status": diagnosis.get("last_known_disease_status"),
            "latest_followup_days": latest_followup.get("days_to_follow_up"),
            "latest_disease_response": latest_followup.get("disease_response")
        })

    print(f"[{min(start + batch_size, len(patient_ids))}/{len(patient_ids)}] "
          f"Retrieved {len(hits)} patients")

df = pd.DataFrame(records)

output = "data/tcga_brca_patient_clinical.csv"
df.to_csv(output, index=False)

print()
print(f"Saved {len(df)} patient records to {output}")
print(f"Columns: {len(df.columns)}")
print("\nMissing values:")
print(df.isna().sum().to_string())
