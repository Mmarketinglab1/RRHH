from uuid import UUID

from pydantic import BaseModel


class CompetencyResult(BaseModel):
    competency_id: UUID
    competency_name: str
    average: float
    weighted_average: float
    median: float
    stddev: float
    responses: int


class ParticipantRanking(BaseModel):
    participant_id: UUID
    participant_name: str
    average: float
    rank: int


class QuestionResult(BaseModel):
    question_id: UUID
    question_text: str
    question_text_self: str | None = None
    question_text_evaluator: str | None = None
    tag_self: str | None = None
    tag_evaluator: str | None = None
    question_type: str
    is_evaluative: bool
    competency_name: str
    average: float | None = None
    median: float | None = None
    stddev: float | None = None
    responses_count: int
    distribution: dict[str, int]


class OutlierAlert(BaseModel):
    evaluator_id: UUID
    evaluator_name: str
    evaluatee_id: UUID
    evaluatee_name: str
    evaluator_average: float
    others_average: float
    diff: float
    alert_type: str  # "high_outlier" | "low_outlier"
    message: str


class EvaluationResults(BaseModel):
    evaluation_id: UUID
    average: float
    median: float
    stddev: float
    competencies: list[CompetencyResult]
    ranking: list[ParticipantRanking]
    questions: list[QuestionResult] = []
    outliers: list[OutlierAlert] = []


class CompetencyScoreByRelation(BaseModel):
    competency_id: UUID
    competency_name: str
    self_score: float | None = None
    evaluators_score: float | None = None
    by_relationship: dict[str, float] = {}
    gap: float | None = None


class QuestionDetailForParticipant(BaseModel):
    question_id: UUID
    question_text: str
    competency_name: str
    question_type: str
    is_evaluative: bool
    self_score: float | None = None
    evaluators_score: float | None = None
    comments: list[dict] = []


class ParticipantDetailResults(BaseModel):
    participant_id: UUID
    participant_name: str
    participant_email: str
    participant_role: str | None = None
    overall_evaluators_score: float | None = None
    overall_self_score: float | None = None
    overall_gap: float | None = None
    competencies: list[CompetencyScoreByRelation] = []
    questions: list[QuestionDetailForParticipant] = []
    top_strengths: list[str] = []
    opportunities: list[str] = []


# ==========================================
# MODELOS PARA REPORTE EJECUTIVO (29 PÁGINAS)
# ==========================================

class ItemScore(BaseModel):
    question_id: UUID
    question_text: str
    competency_id: UUID
    competency_name: str
    average: float
    position: int = 0


class CompetencyDetailedResult(BaseModel):
    competency_id: UUID
    competency_name: str
    weight: float
    weight_pct: float
    net_average: float
    net_median: float
    net_stddev: float
    weighted_average: float
    weighted_median: float
    weighted_stddev: float
    responses_count: int
    items: list[ItemScore] = []


class ParticipantMatrixRow(BaseModel):
    participant_id: UUID
    participant_name: str
    role: str | None = None
    business_line: str | None = None
    performance_history: dict[str, str] = {}
    net_scores: dict[str, float] = {}
    net_average: float
    weighted_scores: dict[str, float] = {}
    weighted_total: float
    rank_net: int = 1
    rank_weighted: int = 1


class ScatterPoint(BaseModel):
    participant_id: UUID
    participant_name: str
    index: int
    business_line: str | None = None
    net_score: float
    weighted_score: float


class BusinessLineResult(BaseModel):
    line_name: str
    count: int
    net_average: float
    net_median: float
    net_stddev: float
    weighted_average: float
    competency_averages: dict[str, float] = {}
    participants: list[ParticipantMatrixRow] = []


class ExecutiveSummaryInsights(BaseModel):
    strongest_competency: str
    weakest_competency: str
    highest_dispersion_competency: str
    lowest_dispersion_competency: str
    summary_bullets: list[str] = []
    reactivos_bullets: list[str] = []


class ExecutiveReportResults(BaseModel):
    evaluation_id: UUID
    evaluation_title: str
    company_name: str
    client_logo_url: str | None = None
    consultant_logo_url: str | None = None
    scale_type: str = "numeric_1_10"
    total_evaluados: int
    net_overall: dict[str, float] = {}
    weighted_overall: dict[str, float] = {}
    thresholds: dict[str, float] = {"high": 8.5, "medium": 7.0}
    competencies: list[CompetencyDetailedResult] = []
    questions: list[ItemScore] = []
    participants_matrix: list[ParticipantMatrixRow] = []
    business_lines: list[BusinessLineResult] = []
    scatter_data: dict[str, list[ScatterPoint]] = {}
    insights: ExecutiveSummaryInsights
