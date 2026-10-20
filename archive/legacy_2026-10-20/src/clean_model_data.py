import csv
from pathlib import Path


input_file = Path(
    "data/processed/model_data_with_calendar_2015_2025.csv"
)

output_file = Path(
    "data/processed/model_data_clean_2015_2025.csv"
)

target = "renewable_share_of_generation_pct"


with input_file.open(
    "r",
    encoding="utf-8",
    newline="",
) as file:
    reader = csv.DictReader(file)
    fieldnames = reader.fieldnames
    rows = list(reader)


clean_rows = [
    row
    for row in rows
    if row[target].strip() != ""
]


with output_file.open(
    "w",
    encoding="utf-8",
    newline="",
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
    )
    writer.writeheader()
    writer.writerows(clean_rows)


print(f"Zeilen vorher: {len(rows)}")
print(
    f"Entfernte Zeilen: "
    f"{len(rows) - len(clean_rows)}"
)
print(f"Zeilen danach: {len(clean_rows)}")
print(f"Erstellt: {output_file}")
