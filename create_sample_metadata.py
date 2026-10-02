from sqlalchemy import text
from database import engine

sql = """
DROP TABLE IF EXISTS sample_metadata;

CREATE TABLE sample_metadata (
    sample_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    sample_type VARCHAR(100)
);

INSERT INTO sample_metadata (sample_id, patient_id, sample_type)
SELECT DISTINCT
    sample_id,
    split_part(sample_id, '-', 1) || '-' ||
    split_part(sample_id, '-', 2) || '-' ||
    split_part(sample_id, '-', 3) AS patient_id,
    sample_type
FROM mirna_expression;

CREATE INDEX idx_sample_metadata_patient
ON sample_metadata(patient_id);

CREATE INDEX idx_sample_metadata_type
ON sample_metadata(sample_type);
"""

with engine.begin() as conn:
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(text(statement))

    count = conn.execute(
        text("SELECT COUNT(*) FROM sample_metadata")
    ).scalar()

    patients = conn.execute(
        text("SELECT COUNT(DISTINCT patient_id) FROM sample_metadata")
    ).scalar()

print(f"SUCCESS: {count} samples added.")
print(f"Unique patients represented: {patients}")
