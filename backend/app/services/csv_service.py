import csv
import re
from io import StringIO


def parse_participants_csv(raw_csv: str) -> list[dict]:
    reader = csv.DictReader(StringIO(raw_csv))
    required = {"email", "full_name"}
    if not reader.fieldnames:
        raise ValueError("El archivo CSV está vacío")

    # Normalizar cabeceras a minúsculas sin espacios
    field_map = {f.strip().lower(): f for f in reader.fieldnames if f}
    
    email_key = next((field_map[k] for k in ["email", "correo", "mail"] if k in field_map), None)
    name_key = next((field_map[k] for k in ["full_name", "nombre", "nombre completo", "colaborador"] if k in field_map), None)

    if not email_key or not name_key:
        raise ValueError("El CSV debe incluir columnas de email y nombre completo (full_name)")

    role_key = next((field_map[k] for k in ["role", "rol", "puesto", "cargo"] if k in field_map), None)
    line_key = next((field_map[k] for k in ["business_line", "linea", "línea", "line", "departamento", "unidad", "area", "área"] if k in field_map), None)

    # Identificar columnas de evaluación o desempeño histórico (ej. 2023, 2024, 2025, ev_2023, etc.)
    perf_col_map: dict[str, str] = {}
    for raw_f in reader.fieldnames:
        clean_f = raw_f.strip().lower()
        match = re.search(r"\b(20[2-3][0-9])\b", clean_f)
        if match:
            year = match.group(1)
            perf_col_map[year] = raw_f

    rows: list[dict] = []
    for row in reader:
        email = (row.get(email_key) or "").strip().lower()
        full_name = (row.get(name_key) or "").strip()
        role = (row.get(role_key) or "").strip() if role_key else None
        business_line = (row.get(line_key) or "").strip() if line_key else None

        perf_history: dict[str, str] = {}
        for year, col_name in perf_col_map.items():
            val = (row.get(col_name) or "").strip()
            if val:
                perf_history[year] = val

        if email and full_name:
            rows.append({
                "email": email,
                "full_name": full_name,
                "role": role or None,
                "business_line": business_line or None,
                "performance_history": perf_history,
            })
    return rows
