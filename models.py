from sqlalchemy import Column, Integer, String, Boolean, Float
from database import Base

class MiRNA(Base):
    __tablename__ = "mirnas"

    id = Column(Integer, primary_key=True, index=True)
    mirna_name = Column(String, unique=True, index=True, nullable=False)
    species = Column(String, default="hsa")

    in_mirbase = Column(Boolean, default=False)
    in_mirdb = Column(Boolean, default=False)
    in_mirnet = Column(Boolean, default=False)
    in_rnainter = Column(Boolean, default=False)
    in_starbase = Column(Boolean, default=False)

    support_count = Column(Integer, default=0)

class MiRNAExpression(Base):
    __tablename__ = "mirna_expression"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String(50), nullable=False, index=True)
    sample_type = Column(String(100), index=True)
    mature_mirna = Column(String(100), nullable=False, index=True)
    precursor_count = Column(Integer)
    read_count_precursor_sum = Column(Float)
    rpm_precursor_sum = Column(Float)
    expression_level = Column(String(50), default="precursor-derived")


class MiRNADifferential(Base):
    __tablename__ = "mirna_differential"

    id = Column(Integer, primary_key=True, index=True)
    mature_mirna = Column(String(100), unique=True, nullable=False, index=True)

    tumor_total_samples = Column(Integer)
    tumor_detected_samples = Column(Integer)
    tumor_detection_rate = Column(Float)
    tumor_mean_rpm = Column(Float)
    tumor_median_rpm = Column(Float)

    normal_total_samples = Column(Integer)
    normal_detected_samples = Column(Integer)
    normal_detection_rate = Column(Float)
    normal_mean_rpm = Column(Float)
    normal_median_rpm = Column(Float)

    fold_change_tumor_over_normal = Column(Float)
    log2_fold_change = Column(Float)
    mann_whitney_u = Column(Float)
    p_value = Column(Float)
    fdr = Column(Float)

    analysis_method = Column(String(100))
    expression_level = Column(String(50))
    note = Column(String)


class PatientClinical(Base):
    __tablename__ = "patient_clinical"

    patient_id = Column(String(50), primary_key=True, index=True)
    sex = Column(String(50))
    age_at_index = Column(Integer)
    age_at_diagnosis_days = Column(Integer)
    race = Column(String(100))
    ethnicity = Column(String(100))
    country_of_residence = Column(String(100))
    year_of_birth = Column(Integer)
    year_of_death = Column(Integer)
    vital_status = Column(String(50))
    primary_site = Column(String(200))
    disease_type = Column(String(200))
    primary_diagnosis = Column(String(300))
    tissue_or_organ_of_origin = Column(String(200))
    site_of_resection_or_biopsy = Column(String(200))
    laterality = Column(String(100))
    tumor_grade = Column(String(100))
    morphology = Column(String(100))
    icd_10_code = Column(String(50))
    classification_of_tumor = Column(String(200))
    sites_of_involvement = Column(String)
    ajcc_staging_system_edition = Column(String(100))
    ajcc_pathologic_stage = Column(String(100))
    ajcc_pathologic_t = Column(String(50))
    ajcc_pathologic_n = Column(String(50))
    ajcc_pathologic_m = Column(String(50))
    metastasis_at_diagnosis = Column(String(200))
    synchronous_malignancy = Column(String(100))
    prior_malignancy = Column(String(100))
    prior_treatment = Column(String(100))
    method_of_diagnosis = Column(String(200))
    year_of_diagnosis = Column(Integer)
    progression_or_recurrence = Column(String(100))
    days_to_recurrence = Column(Integer)
    days_to_diagnosis = Column(Integer)
    days_to_last_follow_up = Column(Integer)
    days_to_last_known_disease_status = Column(Integer)
    last_known_disease_status = Column(String(200))
    latest_followup_days = Column(Integer)
    latest_disease_response = Column(String(200))


class SampleMetadata(Base):
    __tablename__ = "sample_metadata"

    sample_id = Column(String(50), primary_key=True, index=True)
    patient_id = Column(String(50), nullable=False, index=True)
    sample_type = Column(String(100), index=True)
