import pandas as pd
from sqlalchemy import text
from database import engine

csv_file = "data/tcga_brca_patient_clinical.csv"

df = pd.read_csv(csv_file)

# Convert every pandas NaN/NaT to real Python None
# so PostgreSQL receives SQL NULL.
df = df.astype(object)
df = df.where(pd.notna(df), None)

columns = [
    "patient_id",
    "sex",
    "age_at_index",
    "age_at_diagnosis_days",
    "race",
    "ethnicity",
    "country_of_residence",
    "year_of_birth",
    "year_of_death",
    "vital_status",
    "primary_site",
    "disease_type",
    "primary_diagnosis",
    "tissue_or_organ_of_origin",
    "site_of_resection_or_biopsy",
    "laterality",
    "tumor_grade",
    "morphology",
    "icd_10_code",
    "classification_of_tumor",
    "sites_of_involvement",
    "ajcc_staging_system_edition",
    "ajcc_pathologic_stage",
    "ajcc_pathologic_t",
    "ajcc_pathologic_n",
    "ajcc_pathologic_m",
    "metastasis_at_diagnosis",
    "synchronous_malignancy",
    "prior_malignancy",
    "prior_treatment",
    "method_of_diagnosis",
    "year_of_diagnosis",
    "progression_or_recurrence",
    "days_to_recurrence",
    "days_to_diagnosis",
    "days_to_last_follow_up",
    "days_to_last_known_disease_status",
    "last_known_disease_status",
    "latest_followup_days",
    "latest_disease_response"
]

with engine.begin() as conn:

    conn.execute(text("DROP TABLE IF EXISTS patient_clinical"))

    conn.execute(text("""
        CREATE TABLE patient_clinical (
            patient_id VARCHAR(50) PRIMARY KEY,
            sex VARCHAR(30),
            age_at_index INTEGER,
            age_at_diagnosis_days INTEGER,
            race VARCHAR(100),
            ethnicity VARCHAR(100),
            country_of_residence VARCHAR(100),
            year_of_birth INTEGER,
            year_of_death INTEGER,
            vital_status VARCHAR(30),

            primary_site VARCHAR(100),
            disease_type VARCHAR(150),
            primary_diagnosis TEXT,
            tissue_or_organ_of_origin VARCHAR(200),
            site_of_resection_or_biopsy VARCHAR(200),
            laterality VARCHAR(50),
            tumor_grade VARCHAR(100),
            morphology VARCHAR(100),
            icd_10_code VARCHAR(50),
            classification_of_tumor VARCHAR(150),
            sites_of_involvement TEXT,

            ajcc_staging_system_edition VARCHAR(100),
            ajcc_pathologic_stage VARCHAR(100),
            ajcc_pathologic_t VARCHAR(50),
            ajcc_pathologic_n VARCHAR(50),
            ajcc_pathologic_m VARCHAR(50),
            metastasis_at_diagnosis VARCHAR(100),

            synchronous_malignancy VARCHAR(100),
            prior_malignancy VARCHAR(100),
            prior_treatment VARCHAR(100),
            method_of_diagnosis VARCHAR(200),
            year_of_diagnosis INTEGER,
            progression_or_recurrence VARCHAR(100),
            days_to_recurrence INTEGER,

            days_to_diagnosis INTEGER,
            days_to_last_follow_up INTEGER,
            days_to_last_known_disease_status INTEGER,
            last_known_disease_status VARCHAR(200),
            latest_followup_days INTEGER,
            latest_disease_response VARCHAR(200)
        )
    """))

    records = df[columns].to_dict(orient="records")

    insert_sql = text("""
        INSERT INTO patient_clinical (
            patient_id, sex, age_at_index, age_at_diagnosis_days,
            race, ethnicity, country_of_residence, year_of_birth,
            year_of_death, vital_status, primary_site, disease_type,
            primary_diagnosis, tissue_or_organ_of_origin,
            site_of_resection_or_biopsy, laterality, tumor_grade,
            morphology, icd_10_code, classification_of_tumor,
            sites_of_involvement, ajcc_staging_system_edition,
            ajcc_pathologic_stage, ajcc_pathologic_t,
            ajcc_pathologic_n, ajcc_pathologic_m,
            metastasis_at_diagnosis, synchronous_malignancy,
            prior_malignancy, prior_treatment, method_of_diagnosis,
            year_of_diagnosis, progression_or_recurrence,
            days_to_recurrence, days_to_diagnosis,
            days_to_last_follow_up,
            days_to_last_known_disease_status,
            last_known_disease_status, latest_followup_days,
            latest_disease_response
        )
        VALUES (
            :patient_id, :sex, :age_at_index, :age_at_diagnosis_days,
            :race, :ethnicity, :country_of_residence, :year_of_birth,
            :year_of_death, :vital_status, :primary_site, :disease_type,
            :primary_diagnosis, :tissue_or_organ_of_origin,
            :site_of_resection_or_biopsy, :laterality, :tumor_grade,
            :morphology, :icd_10_code, :classification_of_tumor,
            :sites_of_involvement, :ajcc_staging_system_edition,
            :ajcc_pathologic_stage, :ajcc_pathologic_t,
            :ajcc_pathologic_n, :ajcc_pathologic_m,
            :metastasis_at_diagnosis, :synchronous_malignancy,
            :prior_malignancy, :prior_treatment, :method_of_diagnosis,
            :year_of_diagnosis, :progression_or_recurrence,
            :days_to_recurrence, :days_to_diagnosis,
            :days_to_last_follow_up,
            :days_to_last_known_disease_status,
            :last_known_disease_status, :latest_followup_days,
            :latest_disease_response
        )
    """)

    # Insert in batches to make failures easier to diagnose
    batch_size = 100

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        conn.execute(insert_sql, batch)
        print(f"Imported {min(start + batch_size, len(records))}/{len(records)}")

print()

with engine.connect() as conn:
    count = conn.execute(
        text("SELECT COUNT(*) FROM patient_clinical")
    ).scalar()

print(f"SUCCESS: {count} patients imported into patient_clinical.")
