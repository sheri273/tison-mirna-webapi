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
