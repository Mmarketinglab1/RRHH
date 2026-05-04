import csv
from io import StringIO


def parse_participants_csv(raw_csv: str) -> list[dict[str, str | None]]:
    reader = csv.DictReader(StringIO(raw_csv))
    required = {"email", "full_name"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise ValueError("CSV must include email and full_name columns")

    rows: list[dict[str, str | None]] = []
    for row in reader:
        email = (row.get("email") or "").strip().lower()
        full_name = (row.get("full_name") or "").strip()
        role = (row.get("role") or "").strip() or None
        if email and full_name:
            rows.append({"email": email, "full_name": full_name, "role": role})
    return rows
