"use client";

import { Send } from "lucide-react";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { api, PublicSurvey } from "@/lib/api";

export default function SurveyPage() {
  const params = useParams<{ token: string }>();
  const [survey, setSurvey] = useState<PublicSurvey | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<
    Record<string, { score?: number | null; selected_option?: string; selected_options?: string[]; no_observed?: boolean }>
  >({});

  useEffect(() => {
    async function loadSurvey() {
      try {
        setSurvey(await api<PublicSurvey>(`/surveys/public/${params.token}`));
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Encuesta no disponible");
      } finally {
        setLoading(false);
      }
    }
    void loadSurvey();
  }, [params.token]);

  async function submitSurvey(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!survey) return;
    setLoading(true);
    setMessage("");

    // Validar que todas las preguntas tengan respuesta
    const missingQuestion = survey.questions.find((question) => {
      const ans = answers[question.id];
      if (!ans) return true;

      const qType = question.question_type;
      if (qType === "numeric_1_10" || qType === "nps" || qType === "semantic_differential") {
        return ans.score === undefined && !ans.no_observed;
      }
      if (
        qType === "dicotomic" ||
        qType === "likert" ||
        qType === "single_choice" ||
        qType === "frequency" ||
        qType === "categorization"
      ) {
        return ans.selected_option === undefined;
      }
      if (qType === "multiple_choice" || qType === "checklist") {
        return !ans.selected_options || ans.selected_options.length === 0;
      }
      if (qType === "ranking") {
        const optsCount = Array.isArray(question.options) ? question.options.length : 0;
        return !ans.selected_options || ans.selected_options.length !== optsCount;
      }
      return false;
    });

    if (missingQuestion) {
      setMessage("Por favor, responde todas las preguntas del formulario antes de enviar.");
      setLoading(false);
      return;
    }

    const data = new FormData(event.currentTarget);
    const responses = survey.questions.map((question) => ({
      question_id: question.id,
      score: answers[question.id]?.score ?? null,
      selected_option: answers[question.id]?.selected_option ?? null,
      selected_options: answers[question.id]?.selected_options ?? null,
      comment: String(data.get(`comment_${question.id}`) || ""),
    }));

    try {
      await api(`/surveys/public/${params.token}/responses`, {
        method: "POST",
        body: JSON.stringify({ responses }),
      });
      setMessage("Respuestas enviadas correctamente.");
      setAnswers({});
      event.currentTarget.reset();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudieron enviar respuestas");
    } finally {
      setLoading(false);
    }
  }

  function renderQuestionInput(question: PublicSurvey["questions"][number]) {
    const qType = question.question_type;
    const ans = answers[question.id] || {};

    if (qType === "numeric_1_10") {
      return (
        <div className="field">
          <label>Puntaje 1 a 4</label>
          <div className="rating-options" style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {[1, 2, 3, 4].map((num) => (
              <button
                key={num}
                type="button"
                className={`rating-btn ${ans.score === num ? "selected" : ""}`}
                onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: { score: num, no_observed: false } }))}
              >
                {num}
              </button>
            ))}
            {survey?.relationship !== "self" && (
              <button
                type="button"
                className={`rating-btn ${ans.score === null && ans.no_observed ? "selected" : ""}`}
                style={{ borderRadius: 10, width: "auto", padding: "0 14px" }}
                onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: { score: null, no_observed: true } }))}
              >
                No observado
              </button>
            )}
          </div>
        </div>
      );
    }

    if (qType === "nps") {
      return (
        <div className="field">
          <label>Puntaje 0 a 10 (Net Promoter Score)</label>
          <div className="rating-options">
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
              <button
                key={num}
                type="button"
                className={`rating-btn ${ans.score === num ? "selected" : ""}`}
                onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: { score: num } }))}
              >
                {num}
              </button>
            ))}
          </div>
          <div className="row" style={{ justifyContent: "space-between", marginTop: 4, fontSize: "0.8rem" }}>
            <span className="muted">0: Nada probable</span>
            <span className="muted">10: Muy probable</span>
          </div>
        </div>
      );
    }

    if (qType === "dicotomic") {
      return (
        <div className="field">
          <label>Selecciona una opción</label>
          <div className="choice-options">
            {["Sí", "No"].map((opt) => (
              <button
                key={opt}
                type="button"
                className={`choice-btn ${ans.selected_option === opt ? "selected" : ""}`}
                onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: { selected_option: opt } }))}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      );
    }

    if (
      qType === "likert" ||
      qType === "single_choice" ||
      qType === "frequency" ||
      qType === "categorization"
    ) {
      const opts = Array.isArray(question.options)
        ? question.options
        : qType === "likert"
        ? ["Muy en desacuerdo", "En desacuerdo", "Neutral", "De acuerdo", "Muy de acuerdo"]
        : [];
      return (
        <div className="field">
          <label>Selecciona una opción</label>
          <div className="choice-options vertical">
            {opts.map((opt: string) => (
              <button
                key={opt}
                type="button"
                className={`choice-btn list-btn ${ans.selected_option === opt ? "selected" : ""}`}
                onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: { selected_option: opt } }))}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      );
    }

    if (qType === "multiple_choice" || qType === "checklist") {
      const opts = Array.isArray(question.options) ? question.options : [];
      const selectedList = ans.selected_options || [];
      return (
        <div className="field">
          <label>Selecciona una o más opciones</label>
          <div className="choice-options vertical">
            {opts.map((opt: string) => {
              const isSelected = selectedList.includes(opt);
              return (
                <button
                  key={opt}
                  type="button"
                  className={`choice-btn list-btn checkbox-btn ${isSelected ? "selected" : ""}`}
                  onClick={() => {
                    const next = isSelected
                      ? selectedList.filter((o) => o !== opt)
                      : [...selectedList, opt];
                    setAnswers((prev) => ({ ...prev, [question.id]: { selected_options: next } }));
                  }}
                >
                  <span className="checkbox-box">{isSelected ? "✓" : ""}</span>
                  {opt}
                </button>
              );
            })}
          </div>
        </div>
      );
    }

    if (qType === "semantic_differential") {
      const optObj =
        question.options && typeof question.options === "object"
          ? question.options
          : { left_label: "Muy malo", right_label: "Muy bueno", steps: 7 };
      const steps = optObj.steps || 7;
      const stepNums = Array.from({ length: steps }, (_, i) => i + 1);
      return (
        <div className="field">
          <label>Selecciona un punto en la escala</label>
          <div className="semantic-differential">
            <span className="semantic-label left">{optObj.left_label}</span>
            <div className="rating-options">
              {stepNums.map((num) => (
                <button
                  key={num}
                  type="button"
                  className={`rating-btn ${ans.score === num ? "selected" : ""}`}
                  onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: { score: num } }))}
                >
                  {num}
                </button>
              ))}
            </div>
            <span className="semantic-label right">{optObj.right_label}</span>
          </div>
        </div>
      );
    }

    if (qType === "ranking") {
      const opts = Array.isArray(question.options) ? question.options : [];
      const selectedList = ans.selected_options || [];
      return (
        <div className="field">
          <label>Ordena por prioridad (toca en orden de importancia)</label>
          <div className="ranking-instructions">
            <div className="choice-options vertical">
              {opts.map((opt: string) => {
                const idx = selectedList.indexOf(opt);
                const isSelected = idx !== -1;
                return (
                  <button
                    key={opt}
                    type="button"
                    className={`choice-btn list-btn ranking-btn ${isSelected ? "selected" : ""}`}
                    onClick={() => {
                      const next = isSelected
                        ? selectedList.filter((o) => o !== opt)
                        : [...selectedList, opt];
                      setAnswers((prev) => ({ ...prev, [question.id]: { selected_options: next } }));
                    }}
                  >
                    {isSelected && <span className="rank-badge">#{idx + 1}</span>}
                    {opt}
                  </button>
                );
              })}
            </div>
            {selectedList.length > 0 && (
              <button
                type="button"
                className="button secondary mini-btn"
                style={{ marginTop: 8, fontSize: "0.8rem", padding: "4px 8px" }}
                onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: { selected_options: [] } }))}
              >
                Reiniciar orden
              </button>
            )}
          </div>
        </div>
      );
    }

    return null;
  }

  return (
    <main className="shell survey-shell">
      <header className="topbar">
        <div className="brand">
          <img src="/logo-mmarketing.png" alt="Mmarketing Logo" style={{ height: 28, objectFit: "contain" }} />
          <span>Encuesta 360</span>
        </div>
      </header>
      <section className="content">
        <div className="page-title">
          <div>
            <span className="eyebrow">Encuesta confidencial</span>
            <h1>{survey?.evaluation_title || "Encuesta"}</h1>
            {survey && (
              <p className="muted">
                Evaluador: {survey.evaluator_name} | Evaluado: {survey.evaluatee_name}
              </p>
            )}
          </div>
        </div>

        {message && <p className={message.includes("correctamente") ? "success" : "error"}>{message}</p>}
        {loading && <p className="muted">Cargando...</p>}

        {survey && (
          <form className="form" onSubmit={submitSurvey}>
            {survey.questions.map((question) => (
              <section className="panel survey-card" key={question.id}>
                <span className="status-pill">{question.competency}</span>
                <h3 style={{ marginTop: 12 }}>{question.text}</h3>
                
                {renderQuestionInput(question)}

                <div className="field" style={{ marginTop: 16 }}>
                  <label>Comentario (opcional)</label>
                  <textarea
                    className="textarea"
                    name={`comment_${question.id}`}
                    placeholder="Describe brevemente el porqué de tu respuesta..."
                  />
                </div>
              </section>
            ))}
            <button className="button survey-submit" disabled={loading} type="submit">
              <Send size={16} />
              Enviar respuestas
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
