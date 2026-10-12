from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import Evaluation
from app.schemas.auth import CurrentUser
from app.schemas.evaluation import EvaluationCreate, EvaluationRead, EvaluationUpdate

router = APIRouter()


@router.post("", response_model=EvaluationRead)
def create_evaluation(
    payload: EvaluationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Evaluation:
    evaluation = Evaluation(
        company_id=current_user.company_id,
        title=payload.title,
        description=payload.description,
        assessment_type=payload.assessment_type or "individual_contributor",
        client_logo_url=payload.client_logo_url,
        consultant_logo_url=payload.consultant_logo_url,
        scale_type=payload.scale_type or "numeric_1_10",
        score_thresholds=payload.score_thresholds or {"high": 8.5, "medium": 7.0},
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        created_by=current_user.id,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.get("", response_model=list[EvaluationRead])
def list_evaluations(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Evaluation]:
    return list(
        db.scalars(
            select(Evaluation)
            .where(Evaluation.company_id == current_user.company_id)
            .order_by(Evaluation.created_at.desc())
        )
    )


@router.get("/{evaluation_id}", response_model=EvaluationRead)
def get_evaluation(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Evaluation:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.patch("/{evaluation_id}", response_model=EvaluationRead)
def update_evaluation(
    evaluation_id: UUID,
    payload: EvaluationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Evaluation:
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(evaluation, field, value)
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.post("/{evaluation_id}/seed-demo")
def seed_demo_data(
    evaluation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or evaluation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    from app.models.evaluation import Competency, Question
    from app.models.participant import EvaluatorAssignment, Participant
    from app.models.response import Response, SurveyToken
    from app.services.token_service import create_survey_token

    # 1. Crear Competencias básicas si no existen
    comp_defs = [
        ("Liderazgo", "Capacidad para guiar, motivar y empoderar al equipo hacia el logro de metas."),
        ("Comunicación", "Transmisión clara, estructurada y empática de información e ideas."),
        ("Trabajo en Equipo", "Colaboración activa y fomentación de un ambiente de apoyo mutuo."),
        ("Resolución de Problemas", "Identificación analítica de causas raíz y propuesta de soluciones eficaces."),
    ]
    created_comps = []
    for comp_name, comp_desc in comp_defs:
        comp = db.scalar(
            select(Competency).where(
                Competency.company_id == current_user.company_id,
                Competency.evaluation_id == evaluation_id,
                Competency.name == comp_name,
            )
        )
        if not comp:
            comp = Competency(
                company_id=current_user.company_id,
                evaluation_id=evaluation_id,
                name=comp_name,
                description=comp_desc,
                weight=1.0,
            )
            db.add(comp)
            db.flush()
        created_comps.append(comp)

    # 2. Crear Preguntas
    question_defs = [
        (created_comps[0].id, "¿Demuestra capacidad para guiar y motivar al equipo?", "¿Demuestro capacidad para guiar y motivar al equipo?", "¿Demuestra capacidad para guiar y motivar al equipo?", "P1 Auto", "P1 Evaluador"),
        (created_comps[1].id, "¿Transmite ideas y expectativas de forma clara y respetuosa?", "¿Transmito ideas y expectativas de forma clara y respetuosa?", "¿Transmite ideas y expectativas de forma clara y respetuosa?", "P2 Auto", "P2 Evaluador"),
        (created_comps[2].id, "¿Colabora activamente en tareas grupales y fomenta el apoyo mutuo?", "¿Colaboro activamente en tareas grupales y fomento el apoyo mutuo?", "¿Colabora activamente en tareas grupales y fomenta el apoyo mutuo?", "P3 Auto", "P3 Evaluador"),
        (created_comps[3].id, "¿Identifica causas raíz y propone soluciones eficaces ante problemas?", "¿Identifico causas raíz y propongo soluciones eficaces ante problemas?", "¿Identifica causas raíz y propone soluciones eficaces ante problemas?", "P4 Auto", "P4 Evaluador"),
    ]
    created_questions = []
    for idx, (c_id, text, text_s, text_e, tag_s, tag_e) in enumerate(question_defs):
        q = db.scalar(
            select(Question).where(
                Question.company_id == current_user.company_id,
                Question.evaluation_id == evaluation_id,
                Question.text == text,
            )
        )
        if not q:
            q = Question(
                company_id=current_user.company_id,
                evaluation_id=evaluation_id,
                competency_id=c_id,
                text=text,
                text_self=text_s,
                text_evaluator=text_e,
                tag_self=tag_s,
                tag_evaluator=tag_e,
                position=idx + 1,
                question_type="numeric_1_10",
                is_evaluative=True,
            )
            db.add(q)
            db.flush()
        created_questions.append(q)

    # 3. Crear 3 Participantes ficticios
    participant_defs = [
        ("sofia.martinez@empresa.com", "Sofía Martínez", "Directora de Producto"),
        ("carlos.benitez@empresa.com", "Carlos Benítez", "Tech Lead / VP Eng"),
        ("mariana.gomez@empresa.com", "Mariana Gómez", "Sr. Product Designer"),
    ]
    participants_map = {}
    for email, name, role in participant_defs:
        p = db.scalar(
            select(Participant).where(
                Participant.company_id == current_user.company_id,
                Participant.evaluation_id == evaluation_id,
                Participant.email == email,
            )
        )
        if not p:
            p = Participant(
                company_id=current_user.company_id,
                evaluation_id=evaluation_id,
                email=email,
                full_name=name,
                role=role,
            )
            db.add(p)
            db.flush()
        participants_map[email] = p

    sofia = participants_map["sofia.martinez@empresa.com"]
    carlos = participants_map["carlos.benitez@empresa.com"]
    mariana = participants_map["mariana.gomez@empresa.com"]

    # 4. Asignaciones
    assignment_defs = [
        (sofia, sofia, "self", 1.0),
        (sofia, carlos, "line_manager", 1.0),
        (sofia, mariana, "peer", 1.0),

        (carlos, carlos, "self", 1.0),
        (carlos, sofia, "line_manager", 1.0),
        (carlos, mariana, "peer", 1.0),

        (mariana, mariana, "self", 1.0),
        (mariana, carlos, "peer", 1.0),
        (mariana, sofia, "line_manager", 1.0),
    ]

    assignments_created = []
    for evaluatee, evaluator, rel, weight in assignment_defs:
        asgn = db.scalar(
            select(EvaluatorAssignment).where(
                EvaluatorAssignment.company_id == current_user.company_id,
                EvaluatorAssignment.evaluation_id == evaluation_id,
                EvaluatorAssignment.evaluatee_id == evaluatee.id,
                EvaluatorAssignment.evaluator_id == evaluator.id,
            )
        )
        if not asgn:
            asgn = EvaluatorAssignment(
                company_id=current_user.company_id,
                evaluation_id=evaluation_id,
                evaluatee_id=evaluatee.id,
                evaluator_id=evaluator.id,
                relationship=rel,
                weight=weight,
            )
            db.add(asgn)
            db.flush()
        assignments_created.append(asgn)

    # 5. Respuestas simuladas con comentarios ricos
    resp_map = {
        (sofia.id, sofia.id): [(4, "Considero que mantengo un ritmo de comunicación sólido con todo el equipo."), (4, ""), (4, ""), (4, "")],
        (sofia.id, carlos.id): [(4, "Sofía tiene una visión impecable del producto y guía al equipo con total claridad."), (4, "Transmite objetivos de forma excelente."), (4, "Excelente trabajo colaborativo."), (3, "")],
        (sofia.id, mariana.id): [(3, "Sofía es accesible y escucha activamente en las sesiones de diseño."), (4, "Comunicación fluida."), (4, "Gran apoyo en decisiones de UX."), (3, "")],

        (carlos.id, carlos.id): [(3, "Considero que aún puedo mejorar la delegación de tareas arquitectónicas."), (3, ""), (3, ""), (3, "")],
        (carlos.id, sofia.id): [(4, "Carlos es el pilar técnico del equipo. Resuelve bloqueos en tiempo récord."), (4, "Excelente comunicación en temas de arquitectura."), (4, "Gran apoyo entre áreas."), (4, "")],
        (carlos.id, mariana.id): [(4, "Carlos siempre busca soluciones creativas ante requerimientos complejos."), (4, "Muy claro en sus explicaciones técnicas."), (4, "Excelente disposición."), (4, "")],

        (mariana.id, mariana.id): [(4, "Propongo diseños enfocados en valor al usuario final."), (4, ""), (4, ""), (4, "")],
        (mariana.id, carlos.id): [(3, "Mariana colabora activamente con el equipo frontend."), (4, "Gran calidad visual y empatía con el usuario."), (3, ""), (4, "")],
        (mariana.id, sofia.id): [(2, "Se recomienda mejorar la puntualidad de entregas en los hitos del sprint."), (2, "Podría comunicar avances de manera más proactiva."), (2, ""), (3, "")],
    }

    responses_saved = 0
    for asgn in assignments_created:
        tup_key = (asgn.evaluatee_id, asgn.evaluator_id)
        scores_comments = resp_map.get(tup_key)
        if not scores_comments:
            continue

        token_stmt = select(SurveyToken).where(SurveyToken.assignment_id == asgn.id)
        st = db.scalar(token_stmt)
        if not st:
            st = create_survey_token(db, asgn)
        st.used_at = st.created_at

        for q_idx, (sc, comm) in enumerate(scores_comments):
            if q_idx >= len(created_questions):
                continue
            q = created_questions[q_idx]

            resp = db.scalar(
                select(Response).where(
                    Response.company_id == current_user.company_id,
                    Response.assignment_id == asgn.id,
                    Response.question_id == q.id,
                )
            )
            if not resp:
                resp = Response(
                    company_id=current_user.company_id,
                    evaluation_id=evaluation_id,
                    assignment_id=asgn.id,
                    question_id=q.id,
                    score=sc,
                    comment=comm if comm else None,
                )
                db.add(resp)
                responses_saved += 1
            else:
                resp.score = sc
                resp.comment = comm if comm else None

    db.commit()

    return {
        "message": "Datos de ejemplo generados correctamente.",
        "participants_created": len(participant_defs),
        "competencies_created": len(comp_defs),
        "assignments_created": len(assignment_defs),
        "responses_created": responses_saved,
    }
