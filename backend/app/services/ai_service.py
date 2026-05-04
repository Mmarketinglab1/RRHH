import json
from uuid import UUID

from openai import OpenAI

from app.core.config import settings
from app.schemas.result import EvaluationResults


def _client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def generate_questions_for_competencies(
    competencies: list[dict], questions_per_competency: int = 3
) -> list[dict]:
    client = _client()
    if not client:
        return [
            {
                "competency_id": item["id"],
                "text": f"Evalua de 1 a 10 el nivel demostrado en {item['name']}.",
            }
            for item in competencies
            for _ in range(questions_per_competency)
        ]

    prompt = {
        "role": "user",
        "content": (
            "Genera preguntas para una evaluacion 360. Responde solo JSON con la forma "
            '{"questions":[{"competency_id":"uuid","text":"pregunta"}]}. '
            "Las preguntas deben medirse en escala 1 a 10, ser observables y no duplicarse. "
            f"Preguntas por competencia: {questions_per_competency}. "
            f"Competencias: {json.dumps(competencies, default=str)}"
        ),
    }
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "Eres experto en People Analytics y evaluaciones 360 B2B.",
            },
            prompt,
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content).get("questions", [])


def generate_individual_insights(
    participant_id: UUID, results: EvaluationResults
) -> dict:
    client = _client()
    payload = results.model_dump(mode="json")
    if not client:
        return {
            "participant_id": str(participant_id),
            "fortalezas": ["Competencias con promedio superior al promedio general."],
            "areas_de_mejora": ["Competencias con mayor dispersion o menor promedio."],
            "insights": ["Fallback local: configura OPENAI_API_KEY para insights reales."],
        }

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "Eres CTO de un SaaS HRTech y consultor senior de talento.",
            },
            {
                "role": "user",
                "content": (
                    "Genera un reporte individual 360 en JSON con fortalezas, "
                    "areas_de_mejora e insights accionables. "
                    f"participant_id={participant_id}. Resultados: {json.dumps(payload)}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content or "{}")


def generate_group_summary(results: EvaluationResults) -> dict:
    client = _client()
    payload = results.model_dump(mode="json")
    if not client:
        return {
            "fortalezas_grupales": ["Competencias con mejor promedio relativo."],
            "areas_de_mejora_grupales": ["Competencias con menor promedio o alta dispersion."],
            "insights": ["Fallback local: configura OPENAI_API_KEY para resumen grupal real."],
        }

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "Eres experto en People Analytics para organizaciones B2B.",
            },
            {
                "role": "user",
                "content": (
                    "Genera resumen grupal 360 en JSON con fortalezas_grupales, "
                    "areas_de_mejora_grupales e insights. "
                    f"Resultados agregados: {json.dumps(payload)}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content or "{}")
