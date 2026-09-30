#!/usr/bin/env bash
set -e

BASE="$HOME/tison_mirna_api"
cd "$BASE"

mkdir -p data/gdc_quant
mkdir -p data/mapping
mkdir -p data/results

echo "=========================================="
echo "TISON miRNA PIPELINE"
echo "=========================================="

echo
echo "[1/7] Checking project..."
python --version
echo "Project: $BASE"

echo
echo "[2/7] Checking database..."
PGPASSWORD='mirna123' psql -U tison_user -h localhost \
  -d tison_mirna_db \
  -c "SELECT COUNT(*) AS mirna_rows FROM mirnas;"

echo
echo "[3/7] Locating GDC metadata..."

META="brca_mirna_quant_metadata.json"

if [ ! -s "$META" ]; then
    echo "Metadata file not found."
    echo "Downloading fresh TCGA-BRCA miRNA metadata..."

    curl -L --max-time 120 -sS \
      -X POST \
      "https://api.gdc.cancer.gov/files" \
      -H "Content-Type: application/json" \
      -d '{
        "filters":{
          "op":"and",
          "content":[
            {
              "op":"in",
              "content":{
                "field":"cases.project.project_id",
                "value":["TCGA-BRCA"]
              }
            },
            {
              "op":"in",
              "content":{
                "field":"files.data_type",
                "value":["miRNA Expression Quantification"]
              }
            },
            {
              "op":"in",
              "content":{
                "field":"files.experimental_strategy",
                "value":["miRNA-Seq"]
              }
            }
          ]
        },
        "format":"JSON",
        "size":"2000",
        "fields":"file_id,file_name,cases.case_id,cases.samples.sample_type,data_type,experimental_strategy"
      }' \
      -o "$META"
fi

echo "Metadata:"
ls -lh "$META"

echo
echo "[4/7] Extracting GDC file IDs..."

python - <<'PY'
import json
from pathlib import Path

meta = Path("brca_mirna_quant_metadata.json")

obj = json.loads(meta.read_text())

hits = obj.get("data", {}).get("hits", [])

print("Metadata records:", len(hits))

with open("data/mapping/gdc_files.tsv", "w") as out:
    out.write("file_id\tfile_name\tsample_type\tcase_id\n")

    for x in hits:
        fid = x.get("file_id", "")
        fname = x.get("file_name", "")
        cases = x.get("cases", [])

        case_id = ""
        sample_type = ""

        if cases:
            case_id = cases[0].get("case_id", "")

            samples = cases[0].get("samples", [])
            if samples:
                sample_type = samples[0].get("sample_type", "")

        if fid:
            out.write(
                f"{fid}\t{fname}\t{sample_type}\t{case_id}\n"
            )

print("File list created.")
PY

wc -l data/mapping/gdc_files.tsv

echo
echo "[5/7] Downloading GDC miRNA expression files..."

tail -n +2 data/mapping/gdc_files.tsv |
while IFS=$'\t' read -r FILE_ID FILE_NAME SAMPLE_TYPE CASE_ID
do
    OUT="data/gdc_quant/${FILE_ID}.txt"

    if [ -s "$OUT" ]; then
        continue
    fi

    echo "Downloading $FILE_ID"

    curl -L --fail --silent --show-error \
      --max-time 180 \
      "https://api.gdc.cancer.gov/data/${FILE_ID}" \
      -o "$OUT" || rm -f "$OUT"

done

echo
echo "Downloaded files:"
find data/gdc_quant -type f -size +0c | wc -l

echo
echo "[6/7] Extracting all TCGA precursor IDs..."

find data/gdc_quant -type f -size +0c -print0 |
while IFS= read -r -d '' F
do
    awk 'NR > 1 && $1 ~ /^hsa-/ {print $1}' "$F"
done |
sort -u > data/mapping/tcga_precursors.txt

echo "Unique precursor IDs:"
wc -l data/mapping/tcga_precursors.txt

echo
echo "First precursor IDs:"
head -20 data/mapping/tcga_precursors.txt

echo
echo "[7/7] Checking expression files..."

python - <<'PY'
from pathlib import Path

files = list(Path("data/gdc_quant").glob("*.txt"))

total_rows = 0

for f in files[:10]:
    try:
        total_rows += sum(1 for _ in f.open()) - 1
    except:
        pass

print("Expression files available:", len(files))
print("Rows checked in first 10:", total_rows)

if files:
    print("Example file:", files[0])
    print("Example header:")
    print(files[0].read_text(errors="ignore").splitlines()[0])
PY

echo
echo "=========================================="
echo "PIPELINE STAGE 1 COMPLETE"
echo "=========================================="
echo
echo "GDC files:"
find data/gdc_quant -type f -size +0c | wc -l
echo
echo "Unique TCGA precursor IDs:"
wc -l data/mapping/tcga_precursors.txt
echo
echo "Next stage: miRBase-21 precursor → mature miRNA mapping."
