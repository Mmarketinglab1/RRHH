from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import openpyxl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Evaluation
from app.models.participant import EvaluatorAssignment, Participant
from app.schemas.auth import CurrentUser
from app.schemas.participant import (
    AssignmentCreate,
    AssignmentRead,
    CSVUploadResult,
    ParticipantCreate,
    ParticipantRead,
    ParticipantUpdate,
)
from app.services.csv_service import parse_participants_csv

router = APIRouter()


def _ensure_evaluation(db: Session, company_id: UUID, evaluation_id: UUID) -> None:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")


@router.post("/{evaluation_id}/participants", response_model=ParticipantRead)
def create_participant(
    evaluation_id: UUID,
    payload: ParticipantCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Participant:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    
    # Evitar duplicados
    email = payload.email.lower()
    exists = db.scalar(
        select(Participant).where(
            Participant.company_id == current_user.company_id,
            Participant.evaluation_id == evaluation_id,
            Participant.email == email,
        )
    )
    if exists:
        raise HTTPException(status_code=400, detail="Este participante ya está registrado en esta evaluación")

    participant = Participant(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        email=email,
        full_name=payload.full_name,
        role=payload.role,
        business_line=payload.business_line,
        performance_history=payload.performance_history,
    )
    db.add(participant)
    db.flush()  # Generar ID del participante
    
    # Auto-crear asignación de autoevaluación (self)
    auto_assignment = EvaluatorAssignment(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        evaluatee_id=participant.id,
        evaluator_id=participant.id,
        relationship="self",
        weight=1.0,
    )
    db.add(auto_assignment)
    db.commit()
    db.refresh(participant)
    return participant


@router.post("/{evaluation_id}/participants/csv", response_model=CSVUploadResult)
async def upload_participants_csv(
    evaluation_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CSVUploadResult:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    rows = parse_participants_csv((await file.read()).decode("utf-8-sig"))
    created = 0
    skipped = 0
    for row in rows:
        email = row["email"].lower()
        exists = db.scalar(
            select(Participant).where(
                Participant.company_id == current_user.company_id,
                Participant.evaluation_id == evaluation_id,
                Participant.email == email,
            )
        )
        if exists:
            skipped += 1
            continue
        
        participant = Participant(
            company_id=current_user.company_id,
            evaluation_id=evaluation_id,
            email=email,
            full_name=row["full_name"],
            role=row.get("role"),
            business_line=row.get("business_line"),
            performance_history=row.get("performance_history", {}),
        )
        db.add(participant)
        db.flush()  # Generar ID
        
        # Auto-crear autoevaluación
        auto_assignment = EvaluatorAssignment(
            company_id=current_user.company_id,
            evaluation_id=evaluation_id,
            evaluatee_id=participant.id,
            evaluator_id=participant.id,
            relationship="self",
            weight=1.0,
        )
        db.add(auto_assignment)
        created += 1
    db.commit()
    return CSVUploadResult(created=created, skipped=skipped)


@router.get("/{evaluation_id}/participants", response_model=list[ParticipantRead])
def list_participants(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Participant]:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    return list(
        db.scalars(
            select(Participant).where(
                Participant.company_id == current_user.company_id,
                Participant.evaluation_id == evaluation_id,
            )
        )
    )


@router.patch("/{evaluation_id}/participants/{participant_id}", response_model=ParticipantRead)
def update_participant(
    evaluation_id: UUID,
    participant_id: UUID,
    payload: ParticipantUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Participant:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    participant = db.get(Participant, participant_id)
    if (
        not participant
        or participant.company_id != current_user.company_id
        or participant.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Participant not found")

    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates and updates["email"] is not None:
        email = updates["email"].lower()
        if email != participant.email:
            exists = db.scalar(
                select(Participant).where(
                    Participant.company_id == current_user.company_id,
                    Participant.evaluation_id == evaluation_id,
                    Participant.email == email,
                )
            )
            if exists:
                raise HTTPException(status_code=400, detail="Este email ya está registrado para otro participante en esta evaluación")
        updates["email"] = email

    for field, value in updates.items():
        setattr(participant, field, value)
    db.commit()
    db.refresh(participant)
    return participant


@router.delete("/{evaluation_id}/participants/{participant_id}", status_code=204)
def delete_participant(
    evaluation_id: UUID,
    participant_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    participant = db.get(Participant, participant_id)
    if (
        not participant
        or participant.company_id != current_user.company_id
        or participant.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Participant not found")

    db.delete(participant)
    db.commit()


@router.post("/{evaluation_id}/assignments", response_model=AssignmentRead)
def create_assignment(
    evaluation_id: UUID,
    payload: AssignmentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_evaluation(db, current_user.company_id, evaluation_id)

    if payload.evaluatee_id == payload.evaluator_id:
        raise HTTPException(status_code=400, detail="No puedes asignar a un participante como evaluador de sí mismo")

    evaluatee = db.get(Participant, payload.evaluatee_id)
    evaluator = db.get(Participant, payload.evaluator_id)
    if (
        not evaluatee
        or not evaluator
        or evaluatee.company_id != current_user.company_id
        or evaluator.company_id != current_user.company_id
    ):
        raise HTTPException(status_code=404, detail="Participant not found")

    # Evitar asignaciones duplicadas
    exists = db.scalar(
        select(EvaluatorAssignment).where(
            EvaluatorAssignment.company_id == current_user.company_id,
            EvaluatorAssignment.evaluation_id == evaluation_id,
            EvaluatorAssignment.evaluatee_id == payload.evaluatee_id,
            EvaluatorAssignment.evaluator_id == payload.evaluator_id,
        )
    )
    if exists:
        raise HTTPException(status_code=400, detail="Esta asignación ya existe")

    assignment = EvaluatorAssignment(
        company_id=current_user.company_id,
        evaluation_id=evaluation_id,
        evaluatee_id=payload.evaluatee_id,
        evaluator_id=payload.evaluator_id,
        relationship=payload.relationship,
        weight=payload.weight,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    from app.services.token_service import create_survey_token
    survey_token = create_survey_token(db, assignment)

    return {
        "id": assignment.id,
        "evaluation_id": assignment.evaluation_id,
        "evaluatee_id": assignment.evaluatee_id,
        "evaluator_id": assignment.evaluator_id,
        "relationship": assignment.relationship,
        "weight": assignment.weight,
        "is_completed": False,
        "survey_token": survey_token.token,
    }


@router.get("/{evaluation_id}/assignments", response_model=list[AssignmentRead])
def list_assignments(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    
    assignments = db.scalars(
        select(EvaluatorAssignment).where(
            EvaluatorAssignment.company_id == current_user.company_id,
            EvaluatorAssignment.evaluation_id == evaluation_id,
        )
    ).all()

    # Deduplicar asignaciones redundantes en BD (misma pareja evaluatee/evaluator)
    seen_pairs: set[tuple[UUID, UUID]] = set()
    cleaned_assignments = []
    to_delete = []

    for a in assignments:
        pair_key = (a.evaluatee_id, a.evaluator_id)
        if pair_key in seen_pairs:
            to_delete.append(a)
        else:
            seen_pairs.add(pair_key)
            cleaned_assignments.append(a)

    if to_delete:
        for dup in to_delete:
            db.delete(dup)
        db.commit()
        assignments = cleaned_assignments

    # Self-healing logic for missing self-evaluation assignments
    participants = db.scalars(
        select(Participant).where(
            Participant.company_id == current_user.company_id,
            Participant.evaluation_id == evaluation_id,
        )
    ).all()

    has_new_self = False
    for p in participants:
        has_self = any(
            a.evaluatee_id == p.id and a.evaluator_id == p.id
            for a in assignments
        )
        if not has_self:
            auto_self = EvaluatorAssignment(
                company_id=current_user.company_id,
                evaluation_id=evaluation_id,
                evaluatee_id=p.id,
                evaluator_id=p.id,
                relationship="self",
                weight=1.0,
            )
            db.add(auto_self)
            has_new_self = True

    if has_new_self:
        db.commit()
        assignments = db.scalars(
            select(EvaluatorAssignment).where(
                EvaluatorAssignment.company_id == current_user.company_id,
                EvaluatorAssignment.evaluation_id == evaluation_id,
            )
        ).all()

    from app.models.response import SurveyToken
    from app.services.token_service import create_survey_token

    tokens = db.scalars(
        select(SurveyToken).where(
            SurveyToken.company_id == current_user.company_id,
            SurveyToken.evaluation_id == evaluation_id,
        )
    ).all()

    token_map = {t.assignment_id: t for t in tokens}
    results = []
    final_seen = set()

    for assignment in assignments:
        pair_key = (assignment.evaluatee_id, assignment.evaluator_id)
        if pair_key in final_seen:
            continue
        final_seen.add(pair_key)

        survey_token = token_map.get(assignment.id)
        if not survey_token:
            survey_token = create_survey_token(db, assignment)

        results.append({
            "id": assignment.id,
            "evaluation_id": assignment.evaluation_id,
            "evaluatee_id": assignment.evaluatee_id,
            "evaluator_id": assignment.evaluator_id,
            "relationship": assignment.relationship,
            "weight": assignment.weight,
            "is_completed": survey_token.used_at is not None,
            "survey_token": survey_token.token,
        })

    return results


@router.delete("/{evaluation_id}/assignments/{assignment_id}", status_code=204)
def delete_assignment(
    evaluation_id: UUID,
    assignment_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)
    assignment = db.get(EvaluatorAssignment, assignment_id)
    if (
        not assignment
        or assignment.company_id != current_user.company_id
        or assignment.evaluation_id != evaluation_id
    ):
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(assignment)
    db.commit()


@router.get("/{evaluation_id}/participants/import-template")
def download_participants_template(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Participantes y Relaciones"

    headers = [
        "Email Evaluado", 
        "Nombre Evaluado", 
        "Rol Evaluado", 
        "Línea de Negocio",
        "Email Evaluador", 
        "Relacion", 
        "Peso Relacion (%)",
        "Desempeño 2023",
        "Desempeño 2024",
        "Desempeño 2025",
    ]
    ws.append(headers)

    # Filas de ejemplo
    ws.append([
        "laura@ejemplo.com",
        "Laura Esparza",
        "SR",
        "Diabetes",
        "mguinea@ejemplo.com",
        "Líder directo",
        100,
        "Successful",
        "Outperformed",
        "Successful",
    ])
    ws.append([
        "laura@ejemplo.com",
        "Laura Esparza",
        "SR",
        "Diabetes",
        "pedro@ejemplo.com",
        "Par",
        50,
        "Successful",
        "Outperformed",
        "Successful",
    ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    filename = "modelo_participantes_relaciones.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )


@router.post("/{evaluation_id}/participants/import")
async def import_participants_xlsx(
    evaluation_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)

    try:
        content = await file.read()
        wb = openpyxl.load_workbook(filename=BytesIO(content), data_only=True)
    except Exception:
        raise HTTPException(status_code=400, detail="El archivo no es un Excel XLSX válido")

    ws = wb.active
    if not ws:
        raise HTTPException(status_code=400, detail="La hoja de cálculo está vacía")

    participants_created = 0
    assignments_created = 0
    assignments_skipped = 0

    local_participant_cache = {}
    local_assignment_cache = set()

    # Mapeo de relación en español a código de backend
    rel_mapping = {
        "par": "peer",
        "reporte directo": "direct_report",
        "líder directo": "line_manager",
        "lider directo": "line_manager",
        "líder indirecto": "indirect_manager",
        "lider indirecto": "indirect_manager",
        "cliente externo": "external_client",
        "cliente interno": "internal_client",
    }

    # Leer primera fila (cabeceras) para mapeo inteligente
    rows_iter = ws.iter_rows(values_only=True)
    header_row = next(rows_iter, None)
    if not header_row:
        raise HTTPException(status_code=400, detail="La hoja de cálculo no contiene filas")

    header_indices = {}
    perf_col_indices = {}  # year -> col_idx

    for idx, cell_val in enumerate(header_row):
        if not cell_val:
            continue
        clean_text = str(cell_val).strip().lower()
        if any(k in clean_text for k in ["email evaluado", "correo evaluado"]):
            header_indices["eval_email"] = idx
        elif any(k in clean_text for k in ["nombre evaluado", "colaborador"]):
            header_indices["eval_name"] = idx
        elif any(k in clean_text for k in ["rol evaluado", "rol", "puesto"]):
            header_indices["eval_role"] = idx
        elif any(k in clean_text for k in ["línea", "linea", "business line", "unidad", "departamento", "area", "área"]):
            header_indices["eval_line"] = idx
        elif any(k in clean_text for k in ["email evaluador", "correo evaluador"]):
            header_indices["evaluator_email"] = idx
        elif any(k in clean_text for k in ["relacion", "relación"]):
            header_indices["relationship"] = idx
        elif any(k in clean_text for k in ["peso"]):
            header_indices["weight"] = idx

        import re
        year_match = re.search(r"\b(20[2-3][0-9])\b", clean_text)
        if year_match:
            perf_col_indices[year_match.group(1)] = idx

    # Fallbacks si no se identificaron por nombre
    eval_email_idx = header_indices.get("eval_email", 0)
    eval_name_idx = header_indices.get("eval_name", 1)
    eval_role_idx = header_indices.get("eval_role", 2)
    eval_line_idx = header_indices.get("eval_line", 3 if "eval_line" in header_indices else None)
    evaluator_email_idx = header_indices.get("evaluator_email", 4 if eval_line_idx == 3 else 3)
    relationship_idx = header_indices.get("relationship", 5 if eval_line_idx == 3 else 4)
    weight_idx = header_indices.get("weight", 6 if eval_line_idx == 3 else 5)

    for row in rows_iter:
        if not row or len(row) <= eval_email_idx or not row[eval_email_idx]:
            continue

        evaluatee_email = str(row[eval_email_idx]).strip().lower()
        evaluatee_name = str(row[eval_name_idx]).strip() if len(row) > eval_name_idx and row[eval_name_idx] is not None else ""
        evaluatee_role = str(row[eval_role_idx]).strip() if len(row) > eval_role_idx and row[eval_role_idx] is not None else None
        evaluatee_line = str(row[eval_line_idx]).strip() if eval_line_idx is not None and len(row) > eval_line_idx and row[eval_line_idx] is not None else None
        
        evaluator_email = str(row[evaluator_email_idx]).strip().lower() if len(row) > evaluator_email_idx and row[evaluator_email_idx] is not None else None
        relationship_str = str(row[relationship_idx]).strip().lower() if len(row) > relationship_idx and row[relationship_idx] is not None else None
        
        try:
            raw_w = row[weight_idx] if len(row) > weight_idx and row[weight_idx] is not None else 100
            weight_val = float(raw_w) / 100.0 if float(raw_w) > 1.0 else float(raw_w)
        except (ValueError, TypeError):
            weight_val = 1.0

        if not evaluatee_email or not evaluatee_name:
            continue

        # Extraer historial de evaluaciones
        perf_history = {}
        for yr, c_idx in perf_col_indices.items():
            if len(row) > c_idx and row[c_idx] is not None:
                perf_val = str(row[c_idx]).strip()
                if perf_val:
                    perf_history[yr] = perf_val

        # 1. Obtener o crear participante Evaluado
        evaluatee = local_participant_cache.get(evaluatee_email)
        if not evaluatee:
            evaluatee = db.scalar(
                select(Participant).where(
                    Participant.company_id == current_user.company_id,
                    Participant.evaluation_id == evaluation_id,
                    Participant.email == evaluatee_email,
                )
            )
        
        if not evaluatee:
            evaluatee = Participant(
                company_id=current_user.company_id,
                evaluation_id=evaluation_id,
                email=evaluatee_email,
                full_name=evaluatee_name,
                role=evaluatee_role,
                business_line=evaluatee_line,
                performance_history=perf_history,
            )
            db.add(evaluatee)
            db.flush()
            participants_created += 1
            local_participant_cache[evaluatee_email] = evaluatee

            # Auto-crear autoevaluación (self) para el evaluado
            auto_self = EvaluatorAssignment(
                company_id=current_user.company_id,
                evaluation_id=evaluation_id,
                evaluatee_id=evaluatee.id,
                evaluator_id=evaluatee.id,
                relationship="self",
                weight=1.0,
            )
            db.add(auto_self)
            db.flush()
        else:
            # Actualizar campos si vienen en el Excel y no estaban definidos
            if evaluatee_line and not evaluatee.business_line:
                evaluatee.business_line = evaluatee_line
            if perf_history:
                existing_perf = evaluatee.performance_history or {}
                existing_perf.update(perf_history)
                evaluatee.performance_history = existing_perf

        # 2. Si hay evaluador, procesar la asignación (relación)
        if evaluator_email and relationship_str:
            if evaluatee_email == evaluator_email:
                continue  # Evitar registrar autoevaluación manual repetida

            relationship = rel_mapping.get(relationship_str, "peer")

            evaluator = local_participant_cache.get(evaluator_email)
            if not evaluator:
                evaluator = db.scalar(
                    select(Participant).where(
                        Participant.company_id == current_user.company_id,
                        Participant.evaluation_id == evaluation_id,
                        Participant.email == evaluator_email,
                    )
                )
            
            if not evaluator:
                evaluator = Participant(
                    company_id=current_user.company_id,
                    evaluation_id=evaluation_id,
                    email=evaluator_email,
                    full_name=evaluator_email.split("@")[0].capitalize(),
                    role=None,
                )
                db.add(evaluator)
                db.flush()
                participants_created += 1
                local_participant_cache[evaluator_email] = evaluator

                # Auto-crear autoevaluación para el evaluador
                auto_self_eval = EvaluatorAssignment(
                    company_id=current_user.company_id,
                    evaluation_id=evaluation_id,
                    evaluatee_id=evaluator.id,
                    evaluator_id=evaluator.id,
                    relationship="self",
                    weight=1.0,
                )
                db.add(auto_self_eval)
                db.flush()

            # Evitar duplicados en el mismo lote o base de datos
            assignment_key = (evaluatee.id, evaluator.id)
            if assignment_key in local_assignment_cache:
                continue

            assignment_exists = db.scalar(
                select(EvaluatorAssignment).where(
                    EvaluatorAssignment.company_id == current_user.company_id,
                    EvaluatorAssignment.evaluation_id == evaluation_id,
                    EvaluatorAssignment.evaluatee_id == evaluatee.id,
                    EvaluatorAssignment.evaluator_id == evaluator.id,
                )
            )

            if assignment_exists:
                assignment_exists.relationship = relationship
                assignment_exists.weight = weight_val
                assignments_skipped += 1
            else:
                new_assignment = EvaluatorAssignment(
                    company_id=current_user.company_id,
                    evaluation_id=evaluation_id,
                    evaluatee_id=evaluatee.id,
                    evaluator_id=evaluator.id,
                    relationship=relationship,
                    weight=weight_val,
                )
                db.add(new_assignment)
                db.flush()  # Para que db.scalar pueda detectarlo si se repite en el excel
                assignments_created += 1
            
            local_assignment_cache.add(assignment_key)

    db.commit()

    return {
        "participants_created": participants_created,
        "assignments_created": assignments_created,
        "assignments_updated_or_skipped": assignments_skipped,
    }


@router.get("/{evaluation_id}/assignments/export-links")
def export_survey_links(
    evaluation_id: UUID,
    frontend_url: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    _ensure_evaluation(db, current_user.company_id, evaluation_id)

    # 1. Obtener todas las asignaciones
    stmt = (
        select(EvaluatorAssignment)
        .where(
            EvaluatorAssignment.company_id == current_user.company_id,
            EvaluatorAssignment.evaluation_id == evaluation_id,
        )
    )
    assignments = db.scalars(stmt).all()

    # 2. Crear Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Links de Encuestas"

    headers = [
        "Evaluado (Nombre)",
        "Evaluado (Email)",
        "Rol Evaluado",
        "Evaluador (Nombre)",
        "Evaluador (Email)",
        "Relación",
        "Peso (%)",
        "Link de la Encuesta",
    ]
    ws.append(headers)

    from app.services.token_service import create_survey_token
    from app.models.response import SurveyToken

    rel_friendly_names = {
        "self": "Autoevaluación",
        "peer": "Par",
        "direct_report": "Reporte Directo",
        "line_manager": "Líder directo",
        "indirect_manager": "Líder indirecto",
        "external_client": "Cliente Externo",
        "internal_client": "Cliente Interno",
    }

    for assignment in assignments:
        evaluatee = db.get(Participant, assignment.evaluatee_id)
        evaluator = db.get(Participant, assignment.evaluator_id)
        if not evaluatee or not evaluator:
            continue

        # Obtener o crear token de encuesta
        token_stmt = select(SurveyToken).where(SurveyToken.assignment_id == assignment.id)
        survey_token = db.scalar(token_stmt)
        if not survey_token:
            survey_token = create_survey_token(db, assignment)

        # Generar URL pública (asumiendo formato estándar)
        base_url = frontend_url.rstrip("/") if frontend_url else ""
        survey_url = f"{base_url}/survey/{survey_token.token}"

        rel_label = rel_friendly_names.get(assignment.relationship, assignment.relationship)
        weight_pct = int(float(assignment.weight) * 100)

        ws.append([
            evaluatee.full_name,
            evaluatee.email,
            evaluatee.role or "",
            evaluator.full_name,
            evaluator.email,
            rel_label,
            weight_pct,
            survey_url,
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    filename = f"links_encuestas_evaluacion_{evaluation_id}.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
