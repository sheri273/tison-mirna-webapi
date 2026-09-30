import statistics
from scipy.stats import mannwhitneyu
import math
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import SessionLocal
from models import MiRNA, MiRNAExpression, MiRNADifferential

app = FastAPI(title="TISON miRNA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "TISON miRNA API is running"}

@app.get("/mirnas")
def get_mirnas(min_support: int = Query(1, description="Minimum number of supporting databases"),
               limit: int = Query(50, le=500),
               db: Session = Depends(get_db)):
    results = db.query(MiRNA).filter(MiRNA.support_count >= min_support).limit(limit).all()
    return results

@app.get("/mirnas/count")
def count_mirnas(min_support: int = Query(1), db: Session = Depends(get_db)):
    total = db.query(MiRNA).filter(MiRNA.support_count >= min_support).count()
    return {"min_support": min_support, "count": total}

@app.get("/mirnas/{mirna_name}")
def get_mirna(mirna_name: str, db: Session = Depends(get_db)):
    result = db.query(MiRNA).filter(MiRNA.mirna_name == mirna_name).first()
    if not result:
        return {"error": "miRNA not found"}
    return result

from models import MiRNA, MiRNAExpression

@app.get("/expression/search")
def search_expression(
    mirna_name: str | None = None,
    sample_type: str | None = None,
    min_rpm: float | None = None,
    limit: int = Query(100, le=5000),
    db: Session = Depends(get_db)
):
    query = db.query(MiRNAExpression)

    if mirna_name:
        query = query.filter(
            MiRNAExpression.mature_mirna == mirna_name
        )

    if sample_type:
        query = query.filter(
            MiRNAExpression.sample_type == sample_type
        )

    if min_rpm is not None:
        query = query.filter(
            MiRNAExpression.rpm_precursor_sum >= min_rpm
        )

    results = query.limit(limit).all()

    return {
        "filters": {
            "mirna_name": mirna_name,
            "sample_type": sample_type,
            "min_rpm": min_rpm
        },
        "count": len(results),
        "expression_level": "precursor-derived",
        "results": results
    }



@app.get("/expression/compare")
def compare_expression(
    mirna_name: str,
    db: Session = Depends(get_db)
):
    rows = db.query(MiRNAExpression).filter(
        MiRNAExpression.mature_mirna == mirna_name
    ).all()

    tumor_values = [
        row.rpm_precursor_sum
        for row in rows
        if row.sample_type == "Primary Tumor"
        and row.rpm_precursor_sum is not None
    ]

    normal_values = [
        row.rpm_precursor_sum
        for row in rows
        if row.sample_type == "Solid Tissue Normal"
        and row.rpm_precursor_sum is not None
    ]

    if not tumor_values and not normal_values:
        return {
            "mirna": mirna_name,
            "message": "No expression data found"
        }

    tumor_mean = (
        statistics.mean(tumor_values)
        if tumor_values else None
    )

    normal_mean = (
        statistics.mean(normal_values)
        if normal_values else None
    )

    tumor_median = (
        statistics.median(tumor_values)
        if tumor_values else None
    )

    normal_median = (
        statistics.median(normal_values)
        if normal_values else None
    )

    fold_change = None
    log2_fold_change = None
    mann_whitney_u = None
    p_value = None

    if tumor_mean is not None and normal_mean is not None and normal_mean > 0:
        fold_change = tumor_mean / normal_mean
        log2_fold_change = math.log2(fold_change)

    if tumor_values and normal_values:
        test_result = mannwhitneyu(
            tumor_values,
            normal_values,
            alternative="two-sided"
        )
        mann_whitney_u = float(test_result.statistic)
        p_value = float(test_result.pvalue)

    return {
        "mirna": mirna_name,

        "primary_tumor": {
            "detected_samples": len(tumor_values),
            "mean_rpm": tumor_mean,
            "median_rpm": tumor_median,
            "min_rpm": min(tumor_values) if tumor_values else None,
            "max_rpm": max(tumor_values) if tumor_values else None
        },

        "solid_tissue_normal": {
            "detected_samples": len(normal_values),
            "mean_rpm": normal_mean,
            "median_rpm": normal_median,
            "min_rpm": min(normal_values) if normal_values else None,
            "max_rpm": max(normal_values) if normal_values else None
        },

        "comparison": {
            "fold_change_tumor_over_normal": fold_change,
            "log2_fold_change": log2_fold_change,
            "mann_whitney_u": mann_whitney_u,
            "p_value": p_value
        },

        "expression_level": "precursor-derived",

        "note": (
            "GDC miRNA quantification is precursor-derived. "
            "Mapped mature 3p/5p names should not be interpreted "
            "as arm-specific measurements."
        )
    }


@app.get("/expression/differential")
def get_differential_expression(
    mirna_name: str,
    db: Session = Depends(get_db)
):
    """Return precomputed differential expression results for one miRNA."""

    result = db.query(MiRNADifferential).filter(
        MiRNADifferential.mature_mirna == mirna_name
    ).first()

    if result is None:
        return {
            "mirna": mirna_name,
            "message": "No differential expression result found"
        }

    return {
        "mirna": result.mature_mirna,
        "primary_tumor": {
            "total_samples": result.tumor_total_samples,
            "detected_samples": result.tumor_detected_samples,
            "detection_rate_percent": result.tumor_detection_rate,
            "mean_rpm": result.tumor_mean_rpm,
            "median_rpm": result.tumor_median_rpm
        },
        "solid_tissue_normal": {
            "total_samples": result.normal_total_samples,
            "detected_samples": result.normal_detected_samples,
            "detection_rate_percent": result.normal_detection_rate,
            "mean_rpm": result.normal_mean_rpm,
            "median_rpm": result.normal_median_rpm
        },
        "comparison": {
            "fold_change_tumor_over_normal": result.fold_change_tumor_over_normal,
            "log2_fold_change": result.log2_fold_change,
            "mann_whitney_u": result.mann_whitney_u,
            "p_value": result.p_value,
            "fdr": result.fdr
        },
        "analysis_method": result.analysis_method,
        "expression_level": result.expression_level,
        "note": result.note
    }


@app.get("/expression/differential/top")
def get_top_differential_expression(
    limit: int = Query(20, ge=1, le=500),
    sort_by: str = Query("fdr"),
    db: Session = Depends(get_db)
):
    """Return top differential miRNAs."""

    if sort_by == "fdr":
        results = (
            db.query(MiRNADifferential)
            .filter(MiRNADifferential.fdr.isnot(None))
            .order_by(MiRNADifferential.fdr.asc())
            .limit(limit)
            .all()
        )

    elif sort_by == "abs_log2fc":
        results = (
            db.query(MiRNADifferential)
            .filter(
                MiRNADifferential.fdr.isnot(None),
                MiRNADifferential.log2_fold_change.isnot(None)
            )
            .order_by(
                func.abs(MiRNADifferential.log2_fold_change).desc()
            )
            .limit(limit)
            .all()
        )

    elif sort_by == "log2fc":
        results = (
            db.query(MiRNADifferential)
            .filter(MiRNADifferential.log2_fold_change.isnot(None))
            .order_by(MiRNADifferential.log2_fold_change.desc())
            .limit(limit)
            .all()
        )

    else:
        return {
            "error": "sort_by must be one of: fdr, abs_log2fc, log2fc"
        }

    return {
        "count": len(results),
        "sort_by": sort_by,
        "results": [
            {
                "mirna": r.mature_mirna,
                "log2_fold_change": r.log2_fold_change,
                "fold_change": r.fold_change_tumor_over_normal,
                "p_value": r.p_value,
                "fdr": r.fdr
            }
            for r in results
        ]
    }


@app.get("/expression/differential/significant")
def get_significant_differential_expression(
    fdr_threshold: float = Query(0.05, gt=0, le=1),
    direction: str = Query("all"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Return significant differentially expressed miRNAs."""

    query = db.query(MiRNADifferential).filter(
        MiRNADifferential.fdr.isnot(None),
        MiRNADifferential.fdr <= fdr_threshold
    )

    if direction == "up":
        query = query.filter(
            MiRNADifferential.log2_fold_change > 0
        )

    elif direction == "down":
        query = query.filter(
            MiRNADifferential.log2_fold_change < 0
        )

    elif direction != "all":
        return {
            "error": "direction must be one of: all, up, down"
        }

    results = (
        query
        .order_by(MiRNADifferential.fdr.asc())
        .limit(limit)
        .all()
    )

    return {
        "fdr_threshold": fdr_threshold,
        "direction": direction,
        "count": len(results),
        "results": [
            {
                "mirna": r.mature_mirna,
                "log2_fold_change": r.log2_fold_change,
                "fold_change": r.fold_change_tumor_over_normal,
                "p_value": r.p_value,
                "fdr": r.fdr
            }
            for r in results
        ]
    }


@app.get("/expression/{mirna_name}")
def get_expression(
    mirna_name: str,
    sample_type: str | None = None,
    limit: int = Query(100, le=5000),
    db: Session = Depends(get_db)
):
    query = db.query(MiRNAExpression).filter(
        MiRNAExpression.mature_mirna == mirna_name
    )

    if sample_type:
        query = query.filter(
            MiRNAExpression.sample_type == sample_type
        )

    results = query.limit(limit).all()

    return {
        "mirna": mirna_name,
        "sample_type": sample_type,
        "count": len(results),
        "expression_level": "precursor-derived",
        "results": results
    }


@app.get("/expression/{mirna_name}/summary")
def expression_summary(
    mirna_name: str,
    sample_type: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(MiRNAExpression).filter(
        MiRNAExpression.mature_mirna == mirna_name
    )

    if sample_type:
        query = query.filter(
            MiRNAExpression.sample_type == sample_type
        )

    rows = query.all()

    if not rows:
        return {
            "mirna": mirna_name,
            "sample_type": sample_type,
            "count": 0,
            "message": "No expression data found"
        }

    values = [
        row.rpm_precursor_sum
        for row in rows
        if row.rpm_precursor_sum is not None
    ]

    return {
        "mirna": mirna_name,
        "sample_type": sample_type,
        "count": len(values),
        "mean_rpm": sum(values) / len(values),
        "min_rpm": min(values),
        "max_rpm": max(values),
        "expression_level": "precursor-derived",
        "note": "GDC miRNA quantification is precursor-derived; mature 3p/5p values should not be interpreted as arm-specific measurements."
    }


@app.get("/expression/sample/{sample_id}")
def get_sample_expression(
    sample_id: str,
    limit: int = Query(100, le=5000),
    db: Session = Depends(get_db)
):
    results = db.query(MiRNAExpression).filter(
        MiRNAExpression.sample_id == sample_id
    ).limit(limit).all()

    return {
        "sample_id": sample_id,
        "count": len(results),
        "results": results
    }


@app.get("/expression/differential/export")
def export_differential_expression(
    db: Session = Depends(get_db)
):
    """Export all differential expression results as CSV."""
    import csv
    import io
    from fastapi.responses import StreamingResponse

    results = (
        db.query(MiRNADifferential)
        .order_by(MiRNADifferential.mature_mirna.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "mature_mirna",
        "tumor_total_samples",
        "tumor_detected_samples",
        "tumor_detection_rate_percent",
        "tumor_mean_rpm",
        "tumor_median_rpm",
        "normal_total_samples",
        "normal_detected_samples",
        "normal_detection_rate_percent",
        "normal_mean_rpm",
        "normal_median_rpm",
        "fold_change_tumor_over_normal",
        "log2_fold_change",
        "mann_whitney_u",
        "p_value",
        "fdr",
        "analysis_method",
        "expression_level",
        "note"
    ])

    for r in results:
        writer.writerow([
            r.mature_mirna,
            r.tumor_total_samples,
            r.tumor_detected_samples,
            r.tumor_detection_rate,
            r.tumor_mean_rpm,
            r.tumor_median_rpm,
            r.normal_total_samples,
            r.normal_detected_samples,
            r.normal_detection_rate,
            r.normal_mean_rpm,
            r.normal_median_rpm,
            r.fold_change_tumor_over_normal,
            r.log2_fold_change,
            r.mann_whitney_u,
            r.p_value,
            r.fdr,
            r.analysis_method,
            r.expression_level,
            r.note
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=tcga_brca_mirna_differential.csv"
        }
    )
