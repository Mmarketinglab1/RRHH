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
  const [scores, setScores] = useState<Record<string, number>>({});

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

    // Validar que todas las preguntas tengan puntaje
    const missingQuestion = survey.questions.find((question) => !scores[question.id]);
    if (missingQuestion) {
      setMessage("Por favor, asigna un puntaje a todas las preguntas antes de enviar.");
      setLoading(false);
      return;
    }

    const data = new FormData(event.currentTarget);
    const responses = survey.questions.map((question) => ({
      question_id: question.id,
      score: scores[question.id] || 0,
      comment: String(data.get(`comment_${question.id}`) || ""),
    }));

    try {
      await api(`/surveys/public/${params.token}/responses`, {
        method: "POST",
        body: JSON.stringify({ responses }),
      });
      setMessage("Respuestas enviadas correctamente.");
      setScores({});
      event.currentTarget.reset();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudieron enviar respuestas");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell survey-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">360</span>
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
                <div className="field">
                  <label>Puntaje 1 a 10</label>
                  <div className="rating-options">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                      <button
                        key={num}
                        type="button"
                        className={`rating-btn ${scores[question.id] === num ? "selected" : ""}`}
                        onClick={() =>
                          setScores((prev) => ({ ...prev, [question.id]: num }))
                        }
                      >
                        {num}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="field">
                  <label>Comentario (opcional)</label>
                  <textarea
                    className="textarea"
                    name={`comment_${question.id}`}
                    placeholder="Describe brevemente el porqué de tu puntaje..."
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
