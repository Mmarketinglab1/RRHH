from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.evaluation import CompetencyBank
from app.schemas.auth import CurrentUser
from app.schemas.evaluation import CompetencyBankCreate, CompetencyBankRead

router = APIRouter()


@router.get("", response_model=list[CompetencyBankRead])
def list_competency_bank(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CompetencyBank]:
    stmt = (
        select(CompetencyBank)
        .where(
            or_(
                CompetencyBank.company_id == None,
                CompetencyBank.company_id == current_user.company_id,
            )
        )
        .order_by(CompetencyBank.name.asc())
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=CompetencyBankRead)
def create_bank_competency(
    payload: CompetencyBankCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompetencyBank:
    # Verificar duplicados (case-insensitive)
    name_lower = payload.name.strip().lower()
    
    # Comprobar si existe de forma global o en la misma compañía
    exist_stmt = select(CompetencyBank).where(
        func.lower(CompetencyBank.name) == name_lower,
        or_(
            CompetencyBank.company_id == None,
            CompetencyBank.company_id == current_user.company_id,
        )
    )
    exist = db.scalars(exist_stmt).first()
    if exist:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una competencia con este nombre en el banco.",
        )

    bank_comp = CompetencyBank(
        name=payload.name.strip(),
        description=payload.description,
        company_id=current_user.company_id,
    )
    db.add(bank_comp)
    db.commit()
    db.refresh(bank_comp)
    return bank_comp
