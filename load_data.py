import pandas as pd
from database import SessionLocal
from models import MiRNA

# Read the Excel file
df = pd.read_excel("Master_Human_miRNA_List_with_Support_Count.xlsx")

db = SessionLocal()

inserted = 0
skipped = 0

for _, row in df.iterrows():
    existing = db.query(MiRNA).filter(MiRNA.mirna_name == row["miRNA_Name"]).first()
    if existing:
        skipped += 1
        continue

    new_mirna = MiRNA(
        mirna_name=row["miRNA_Name"],
        species="hsa",
        in_mirbase=bool(row["miRBase"]),
        in_mirdb=bool(row["miRDB"]),
        in_mirnet=bool(row["miRNet"]),
        in_rnainter=bool(row["RNAInter"]),
        in_starbase=bool(row["starBase"]),
        support_count=int(row["Database_Count"]),
    )
    db.add(new_mirna)
    inserted += 1

db.commit()
db.close()

print(f"Inserted: {inserted}")
print(f"Skipped (already existed): {skipped}")
