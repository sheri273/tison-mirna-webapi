import math
import statistics
import time

import psycopg2
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests


DB_CONFIG = {
    "host": "127.0.0.1",
    "dbname": "tison_mirna_db",
    "user": "tison_user",
    "password": "mirna123",
}


def main():

    start = time.time()

    print("=" * 70)
    print("TCGA-BRCA ALL-miRNA DIFFERENTIAL EXPRESSION ANALYSIS")
    print("=" * 70)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("\nLoading miRNA expression values...")

    cur.execute("""
        SELECT
            mature_mirna,
            sample_type,
            rpm_precursor_sum
        FROM mirna_expression
        WHERE sample_type IN ('Primary Tumor', 'Solid Tissue Normal')
          AND rpm_precursor_sum IS NOT NULL
        ORDER BY mature_mirna, sample_type
    """)

    rows = cur.fetchall()

    print(f"Rows loaded: {len(rows):,}")

    data = {}

    for mirna, sample_type, rpm in rows:

        if mirna not in data:
            data[mirna] = {
                "Primary Tumor": [],
                "Solid Tissue Normal": []
            }

        data[mirna][sample_type].append(float(rpm))

    print(f"Unique miRNAs: {len(data):,}")

    results = []

    print("\nCalculating statistics...")

    for i, (mirna, groups) in enumerate(data.items(), start=1):

        tumor = groups["Primary Tumor"]
        normal = groups["Solid Tissue Normal"]

        if not tumor or not normal:
            continue

        tumor_detected = sum(v > 0 for v in tumor)
        normal_detected = sum(v > 0 for v in normal)

        tumor_mean = statistics.mean(tumor)
        normal_mean = statistics.mean(normal)

        tumor_median = statistics.median(tumor)
        normal_median = statistics.median(normal)

        fold_change = None
        log2_fc = None

        if tumor_mean > 0 and normal_mean > 0:
            fold_change = tumor_mean / normal_mean
            log2_fc = math.log2(fold_change)

        try:
            test = mannwhitneyu(
                tumor,
                normal,
                alternative="two-sided"
            )

            u_stat = float(test.statistic)
            p_value = float(test.pvalue)

        except Exception:
            u_stat = None
            p_value = None

        results.append({
            "mature_mirna": mirna,

            "tumor_total_samples": len(tumor),
            "tumor_detected_samples": tumor_detected,
            "tumor_detection_rate": (
                100.0 * tumor_detected / len(tumor)
            ),

            "tumor_mean_rpm": tumor_mean,
            "tumor_median_rpm": tumor_median,

            "normal_total_samples": len(normal),
            "normal_detected_samples": normal_detected,
            "normal_detection_rate": (
                100.0 * normal_detected / len(normal)
            ),

            "normal_mean_rpm": normal_mean,
            "normal_median_rpm": normal_median,

            "fold_change": fold_change,
            "log2_fc": log2_fc,

            "mann_whitney_u": u_stat,
            "p_value": p_value
        })

        if i % 250 == 0:
            print(f"Processed: {i:,} miRNAs")

    print(f"\nStatistical results: {len(results):,}")

    # ---------------------------------------------------------
    # Benjamini-Hochberg FDR
    # ---------------------------------------------------------

    valid = [
        r for r in results
        if r["p_value"] is not None
    ]

    pvalues = [r["p_value"] for r in valid]

    print("Calculating Benjamini-Hochberg FDR...")

    if pvalues:
        _, fdr_values, _, _ = multipletests(
            pvalues,
            alpha=0.05,
            method="fdr_bh"
        )

        for result, fdr in zip(valid, fdr_values):
            result["fdr"] = float(fdr)

    # ---------------------------------------------------------
    # Save to PostgreSQL
    # ---------------------------------------------------------

    print("\nSaving results to PostgreSQL...")

    cur.execute("TRUNCATE TABLE mirna_differential RESTART IDENTITY")

    insert_sql = """
        INSERT INTO mirna_differential (
            mature_mirna,
            tumor_total_samples,
            tumor_detected_samples,
            tumor_detection_rate,
            tumor_mean_rpm,
            tumor_median_rpm,
            normal_total_samples,
            normal_detected_samples,
            normal_detection_rate,
            normal_mean_rpm,
            normal_median_rpm,
            fold_change_tumor_over_normal,
            log2_fold_change,
            mann_whitney_u,
            p_value,
            fdr,
            analysis_method,
            expression_level,
            note
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s
        )
    """

    values = []

    for r in results:

        values.append((
            r["mature_mirna"],

            r["tumor_total_samples"],
            r["tumor_detected_samples"],
            r["tumor_detection_rate"],
            r["tumor_mean_rpm"],
            r["tumor_median_rpm"],

            r["normal_total_samples"],
            r["normal_detected_samples"],
            r["normal_detection_rate"],
            r["normal_mean_rpm"],
            r["normal_median_rpm"],

            r["fold_change"],
            r["log2_fc"],

            r["mann_whitney_u"],
            r["p_value"],
            r.get("fdr"),

            "Mann-Whitney U; Benjamini-Hochberg FDR",
            "precursor-derived",

            "GDC TCGA-BRCA miRNA quantification is precursor-derived. "
            "Mapped mature 3p/5p names should not be interpreted "
            "as arm-specific measurements."
        ))

    cur.executemany(insert_sql, values)

    conn.commit()

    print(f"Inserted: {len(values):,} differential results")

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    cur.execute("""
        SELECT COUNT(*)
        FROM mirna_differential
    """)

    count = cur.fetchone()[0]

    print(f"Database rows: {count:,}")

    cur.execute("""
        SELECT
            mature_mirna,
            log2_fold_change,
            p_value,
            fdr
        FROM mirna_differential
        ORDER BY fdr NULLS LAST
        LIMIT 10
    """)

    print("\nTop 10 results by FDR:")
    print("-" * 70)

    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()

    elapsed = time.time() - start

    print("\n" + "=" * 70)
    print(f"ANALYSIS COMPLETE")
    print(f"Time: {elapsed / 60:.2f} minutes")
    print("=" * 70)


if __name__ == "__main__":
    main()
