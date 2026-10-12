from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Evaluation
from app.models.participant import Participant
from app.schemas.auth import CurrentUser
from app.schemas.result import EvaluationResults, ExecutiveReportResults, ParticipantDetailResults
from app.services.results_service import (
    calculate_evaluation_results,
    calculate_executive_report_results,
    calculate_participant_results,
)
from app.services.pdf_service import (
    generate_all_participants_zip,
    generate_executive_29p_report_pdf,
    generate_general_results_pdf,
    generate_participant_results_pdf,
)

router = APIRouter()


@router.get("/{evaluation_id}/results", response_model=EvaluationResults)
def get_results(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvaluationResults:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return calculate_evaluation_results(db, current_user.company_id, evaluation_id)


@router.get("/{evaluation_id}/results/executive", response_model=ExecutiveReportResults)
def get_executive_results(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExecutiveReportResults:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return calculate_executive_report_results(db, current_user.company_id, evaluation_id)


@router.get("/{evaluation_id}/results/executive/pdf")
def export_executive_report_pdf(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    pdf_bytes = generate_executive_29p_report_pdf(db, current_user.company_id, evaluation_id)
    filename = f"Reporte_Ejecutivo_360_{evaluation.title.replace(' ', '_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{evaluation_id}/results/pdf")
def export_general_results_pdf(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    pdf_bytes = generate_general_results_pdf(db, current_user.company_id, evaluation_id)
    filename = f"Informe_General_360_{evaluation.title.replace(' ', '_')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{evaluation_id}/results/participant/{participant_id}", response_model=ParticipantDetailResults)
def get_participant_results(
    evaluation_id: UUID,
    participant_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ParticipantDetailResults:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return calculate_participant_results(db, current_user.company_id, evaluation_id, participant_id)


@router.get("/{evaluation_id}/results/participant/{participant_id}/pdf")
def export_participant_results_pdf(
    evaluation_id: UUID,
    participant_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    participant = db.get(Participant, participant_id)
    if not participant or participant.evaluation_id != evaluation_id or participant.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Participant not found")

    pdf_bytes = generate_participant_results_pdf(db, current_user.company_id, evaluation_id, participant_id)
    clean_name = "".join(c for c in participant.full_name if c.isalnum() or c in (" ", "_", "-")).rstrip()
    filename = f"Informe_360_{clean_name.replace(' ', '_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{evaluation_id}/results/participants/pdf-zip")
def export_all_participants_pdf_zip(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    zip_bytes = generate_all_participants_zip(db, current_user.company_id, evaluation_id)
    filename = f"Informes_360_Todos_{evaluation.title.replace(' ', '_')}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

