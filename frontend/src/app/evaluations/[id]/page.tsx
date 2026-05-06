"use client";

import {
  ArrowLeft,
  Bot,
  ClipboardList,
  Link as LinkIcon,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  X,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  api,
  Assignment,
  Competency,
  Evaluation,
  EvaluationResults,
  Participant,
  Question,
} from "@/lib/api";

export default function EvaluationDetail() {
  const params = useParams<{ id: string }>();
  const evaluationId = params.id;
  const [token, setToken] = useState<string | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [competencies, setCompetencies] = useState<Competency[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [results, setResults] = useState<EvaluationResults | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingCompetencyId, setEditingCompetencyId] = useState<string | null>(null);
  const [editingQuestionId, setEditingQuestionId] = useState<string | null>(null);
  const [editingParticipantId, setEditingParticipantId] = useState<string | null>(null);

  const firstCompetency = competencies[0]?.id || "";

  useEffect(() => {
    const saved = localStorage.getItem("rrhh_token");
    setToken(saved);
  }, []);

  useEffect(() => {
    if (token) {
      void refreshAll(token);
    }
  }, [token]);

  async function refreshAll(authToken = token) {
    if (!authToken) return;
    setLoading(true);
    setMessage("");
    try {
      const [evaluationData, competencyData, questionData, participantData, assignmentData] = await Promise.all([
        api<Evaluation>(`/evaluations/${evaluationId}`, {}, authToken),
        api<Competency[]>(`/evaluations/${evaluationId}/competencies`, {}, authToken),
        api<Question[]>(`/evaluations/${evaluationId}/questions`, {}, authToken),
        api<Participant[]>(`/evaluations/${evaluationId}/participants`, {}, authToken),
        api<Assignment[]>(`/evaluations/${evaluationId}/assignments`, {}, authToken),
      ]);
      setEvaluation(evaluationData);
      setCompetencies(competencyData);
      setQuestions(questionData);
      setParticipants(participantData);
      setAssignments(assignmentData);
      await loadResults(authToken);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo cargar la evaluacion");
    } finally {
      setLoading(false);
    }
  }

  async function loadResults(authToken = token) {
    if (!authToken) return;
    try {
      setResults(await api<EvaluationResults>(`/evaluations/${evaluationId}/results`, {}, authToken));
    } catch {
      setResults(null);
    }
  }

  async function postForm<T>(
    path: string,
    event: FormEvent<HTMLFormElement>,
    payload: Record<string, unknown>,
  ): Promise<T | null> {
    event.preventDefault();
    const form = event.currentTarget;
    if (!token) return null;
    setLoading(true);
    setMessage("");
    try {
      const result = await api<T>(path, { method: "POST", body: JSON.stringify(payload) }, token);
      form.reset();
      await refreshAll(token);
      return result;
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo guardar");
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function addCompetency(event: FormEvent<HTMLFormElement>) {
    const data = new FormData(event.currentTarget);
    await postForm<Competency>(`/evaluations/${evaluationId}/competencies`, event, {
      name: data.get("name"),
      description: data.get("description"),
      weight: Number(data.get("weight") || 1),
    });
  }

  async function addQuestion(event: FormEvent<HTMLFormElement>) {
    const data = new FormData(event.currentTarget);
    await postForm<Question>(`/evaluations/${evaluationId}/questions`, event, {
      competency_id: data.get("competency_id"),
      text: data.get("text"),
      position: Number(data.get("position") || questions.length + 1),
    });
  }

  async function generateQuestions() {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      await api(`/evaluations/${evaluationId}/ai/questions`, { method: "POST" }, token);
      await refreshAll(token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudieron generar preguntas");
    } finally {
      setLoading(false);
    }
  }

  async function addParticipant(event: FormEvent<HTMLFormElement>) {
    const data = new FormData(event.currentTarget);
    await postForm<Participant>(`/evaluations/${evaluationId}/participants`, event, {
      email: data.get("email"),
      full_name: data.get("full_name"),
      role: data.get("role"),
    });
  }

  async function addAssignment(event: FormEvent<HTMLFormElement>) {
    const data = new FormData(event.currentTarget);
    const assignment = await postForm<Assignment>(`/evaluations/${evaluationId}/assignments`, event, {
      evaluatee_id: data.get("evaluatee_id"),
      evaluator_id: data.get("evaluator_id"),
      relationship: data.get("relationship") || "peer",
      weight: Number(data.get("weight") || 1),
    });
    if (assignment) {
      setAssignments((current) => [assignment, ...current]);
    }
  }

  async function generateToken(assignmentId: string) {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      const result = await api<{ public_url: string }>(
        `/surveys/assignments/${assignmentId}/token`,
        { method: "POST" },
        token,
      );
      setMessage(`Link publico: ${window.location.origin}${result.public_url.replace("/surveys/public", "/survey")}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo generar link");
    } finally {
      setLoading(false);
    }
  }

  async function patchResource<T>(path: string, payload: Record<string, unknown>) {
    if (!token) return null;
    setLoading(true);
    setMessage("");
    try {
      const result = await api<T>(path, { method: "PATCH", body: JSON.stringify(payload) }, token);
      await refreshAll(token);
      return result;
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo actualizar");
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function deleteResource(path: string, label: string) {
    if (!token) return;
    if (!window.confirm(`Eliminar ${label}? Esta accion no se puede deshacer.`)) return;
    setLoading(true);
    setMessage("");
    try {
      await api(path, { method: "DELETE" }, token);
      await refreshAll(token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo eliminar");
    } finally {
      setLoading(false);
    }
  }

  async function updateCompetency(event: FormEvent<HTMLFormElement>, competencyId: string) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const updated = await patchResource<Competency>(
      `/evaluations/${evaluationId}/competencies/${competencyId}`,
      {
        name: data.get("name"),
        description: data.get("description"),
        weight: Number(data.get("weight") || 1),
      },
    );
    if (updated) setEditingCompetencyId(null);
  }

  async function updateQuestion(event: FormEvent<HTMLFormElement>, questionId: string) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const updated = await patchResource<Question>(
      `/evaluations/${evaluationId}/questions/${questionId}`,
      {
        competency_id: data.get("competency_id"),
        text: data.get("text"),
        position: Number(data.get("position") || 0),
      },
    );
    if (updated) setEditingQuestionId(null);
  }

  async function updateParticipant(event: FormEvent<HTMLFormElement>, participantId: string) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const updated = await patchResource<Participant>(
      `/evaluations/${evaluationId}/participants/${participantId}`,
      {
        email: data.get("email"),
        full_name: data.get("full_name"),
        role: data.get("role"),
      },
    );
    if (updated) setEditingParticipantId(null);
  }

  const participantOptions = useMemo(
    () =>
      participants.map((participant) => (
        <option key={participant.id} value={participant.id}>
          {participant.full_name}
        </option>
      )),
    [participants],
  );

  if (!token) {
    return (
      <main className="content">
        <p className="error">Necesitas iniciar sesion.</p>
        <Link className="button secondary" href="/">
          Volver
        </Link>
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="topbar">
        <Link className="brand" href="/">
          <span className="brand-mark">360</span>
          <span>RRHH 360 AI</span>
        </Link>
        <button className="button secondary" onClick={() => refreshAll()} type="button">
          <RefreshCw size={16} />
          Actualizar
        </button>
      </header>

      <section className="content">
        <div className="page-title">
          <div>
            <Link className="muted" href="/">
              <ArrowLeft size={14} /> Volver
            </Link>
            <span className="eyebrow">Evaluacion 360</span>
            <h1>{evaluation?.title || "Evaluacion"}</h1>
            <p className="muted">{evaluation?.description || "Sin descripcion"}</p>
          </div>
          <div className="toolbar">
            <span className="status-pill">{competencies.length} competencias</span>
            <span className="status-pill">{participants.length} participantes</span>
          </div>
        </div>

        {message && <p className={message.startsWith("Link") ? "success" : "error"}>{message}</p>}

        <div className="kpi-band">
          <section className="panel metric">
            <span className="muted">Promedio</span>
            <strong>{results?.average ?? 0}</strong>
          </section>
          <section className="panel metric">
            <span className="muted">Mediana</span>
            <strong>{results?.median ?? 0}</strong>
          </section>
          <section className="panel metric">
            <span className="muted">Desvio</span>
            <strong>{results?.stddev ?? 0}</strong>
          </section>
        </div>

        <div className="grid two">
          <section className="panel">
            <h2>Competencias</h2>
            <form className="form" onSubmit={addCompetency} style={{ marginTop: 14 }}>
              <div className="field">
                <label>Nombre</label>
                <input className="input" name="name" required />
              </div>
              <div className="field">
                <label>Descripcion</label>
                <textarea className="textarea" name="description" />
              </div>
              <div className="field">
                <label>Peso</label>
                <input className="input" defaultValue="1" min="0.1" name="weight" step="0.1" type="number" />
              </div>
              <button className="button" disabled={loading} type="submit">
                <Plus size={16} />
                Agregar
              </button>
            </form>
            <div className="list">
              {competencies.map((competency) => (
                <div className="item" key={competency.id}>
                  {editingCompetencyId === competency.id ? (
                    <form className="form" onSubmit={(event) => updateCompetency(event, competency.id)}>
                      <input className="input" defaultValue={competency.name} name="name" required />
                      <textarea className="textarea" defaultValue={competency.description || ""} name="description" />
                      <input className="input" defaultValue={competency.weight} min="0.1" name="weight" step="0.1" type="number" />
                      <div className="toolbar">
                        <button className="button" disabled={loading} type="submit">
                          <Save size={16} />
                          Guardar
                        </button>
                        <button className="button secondary" onClick={() => setEditingCompetencyId(null)} type="button">
                          <X size={16} />
                          Cancelar
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <div className="row">
                        <strong>{competency.name}</strong>
                        <span className="status-pill">Peso {competency.weight}</span>
                      </div>
                      {competency.description && <span className="muted">{competency.description}</span>}
                      <div className="toolbar">
                        <button className="button secondary" onClick={() => setEditingCompetencyId(competency.id)} type="button">
                          <Pencil size={16} />
                          Editar
                        </button>
                        <button
                          className="button danger"
                          onClick={() => deleteResource(`/evaluations/${evaluationId}/competencies/${competency.id}`, "competencia")}
                          type="button"
                        >
                          <Trash2 size={16} />
                          Borrar
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
              {!competencies.length && <div className="empty-state">Agrega competencias para construir el formulario.</div>}
            </div>
          </section>

          <section className="panel">
            <div className="row">
              <h2>Preguntas</h2>
              <button className="button secondary" disabled={loading || !competencies.length} onClick={generateQuestions} type="button">
                <Bot size={16} />
                IA
              </button>
            </div>
            <form className="form" onSubmit={addQuestion} style={{ marginTop: 14 }}>
              <div className="field">
                <label>Competencia</label>
                <select className="select" defaultValue={firstCompetency} name="competency_id" required>
                  {competencies.map((competency) => (
                    <option key={competency.id} value={competency.id}>
                      {competency.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Pregunta</label>
                <textarea className="textarea" name="text" required />
              </div>
              <input name="position" type="hidden" value={questions.length + 1} />
              <button className="button" disabled={loading || !competencies.length} type="submit">
                <Plus size={16} />
                Agregar
              </button>
            </form>
            <div className="list">
              {questions.map((question) => (
                <div className="item" key={question.id}>
                  {editingQuestionId === question.id ? (
                    <form className="form" onSubmit={(event) => updateQuestion(event, question.id)}>
                      <select className="select" defaultValue={question.competency_id} name="competency_id" required>
                        {competencies.map((competency) => (
                          <option key={competency.id} value={competency.id}>
                            {competency.name}
                          </option>
                        ))}
                      </select>
                      <textarea className="textarea" defaultValue={question.text} name="text" required />
                      <input className="input" defaultValue={question.position} name="position" type="number" />
                      <div className="toolbar">
                        <button className="button" disabled={loading} type="submit">
                          <Save size={16} />
                          Guardar
                        </button>
                        <button className="button secondary" onClick={() => setEditingQuestionId(null)} type="button">
                          <X size={16} />
                          Cancelar
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <strong>{question.text}</strong>
                      <span className="muted">Posicion {question.position}</span>
                      <div className="toolbar">
                        <button className="button secondary" onClick={() => setEditingQuestionId(question.id)} type="button">
                          <Pencil size={16} />
                          Editar
                        </button>
                        <button
                          className="button danger"
                          onClick={() => deleteResource(`/evaluations/${evaluationId}/questions/${question.id}`, "pregunta")}
                          type="button"
                        >
                          <Trash2 size={16} />
                          Borrar
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
              {!questions.length && <div className="empty-state">Todavia no hay preguntas configuradas.</div>}
            </div>
          </section>

          <section className="panel">
            <h2>Participantes</h2>
            <form className="form" onSubmit={addParticipant} style={{ marginTop: 14 }}>
              <div className="field">
                <label>Email</label>
                <input className="input" name="email" required type="email" />
              </div>
              <div className="field">
                <label>Nombre</label>
                <input className="input" name="full_name" required />
              </div>
              <div className="field">
                <label>Rol</label>
                <input className="input" name="role" />
              </div>
              <button className="button" disabled={loading} type="submit">
                <Plus size={16} />
                Agregar
              </button>
            </form>
            <div className="list">
              {participants.map((participant) => (
                <div className="item" key={participant.id}>
                  {editingParticipantId === participant.id ? (
                    <form className="form" onSubmit={(event) => updateParticipant(event, participant.id)}>
                      <input className="input" defaultValue={participant.email} name="email" required type="email" />
                      <input className="input" defaultValue={participant.full_name} name="full_name" required />
                      <input className="input" defaultValue={participant.role || ""} name="role" />
                      <div className="toolbar">
                        <button className="button" disabled={loading} type="submit">
                          <Save size={16} />
                          Guardar
                        </button>
                        <button className="button secondary" onClick={() => setEditingParticipantId(null)} type="button">
                          <X size={16} />
                          Cancelar
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <strong>{participant.full_name}</strong>
                      <span className="muted">{participant.email}</span>
                      {participant.role && <span className="status-pill">{participant.role}</span>}
                      <div className="toolbar">
                        <button className="button secondary" onClick={() => setEditingParticipantId(participant.id)} type="button">
                          <Pencil size={16} />
                          Editar
                        </button>
                        <button
                          className="button danger"
                          onClick={() => deleteResource(`/evaluations/${evaluationId}/participants/${participant.id}`, "participante")}
                          type="button"
                        >
                          <Trash2 size={16} />
                          Borrar
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
              {!participants.length && <div className="empty-state">Carga participantes para asignar evaluadores.</div>}
            </div>
          </section>

          <section className="panel">
            <h2>Asignaciones</h2>
            <form className="form" onSubmit={addAssignment} style={{ marginTop: 14 }}>
              <div className="field">
                <label>Evaluado</label>
                <select className="select" name="evaluatee_id" required>
                  {participantOptions}
                </select>
              </div>
              <div className="field">
                <label>Evaluador</label>
                <select className="select" name="evaluator_id" required>
                  {participantOptions}
                </select>
              </div>
              <div className="field">
                <label>Relacion</label>
                <select className="select" name="relationship">
                  <option value="peer">Par</option>
                  <option value="manager">Manager</option>
                  <option value="direct_report">Reporte</option>
                  <option value="self">Autoevaluacion</option>
                </select>
              </div>
              <div className="field">
                <label>Peso</label>
                <input className="input" defaultValue="1" min="0.1" name="weight" step="0.1" type="number" />
              </div>
              <button className="button" disabled={loading || participants.length < 2} type="submit">
                <ClipboardList size={16} />
                Asignar
              </button>
            </form>
            <div className="list">
              {assignments.map((assignment) => (
                <div className="item" key={assignment.id}>
                  <div className="row">
                    <strong>{assignment.relationship}</strong>
                    <button className="button secondary" onClick={() => generateToken(assignment.id)} type="button">
                      <LinkIcon size={16} />
                      Link encuesta
                    </button>
                  </div>
                </div>
              ))}
              {!assignments.length && <div className="empty-state">Crea asignaciones para generar links publicos.</div>}
            </div>
          </section>
        </div>

        <section className="panel" style={{ marginTop: 18 }}>
          <h2>Resultados</h2>
          <div className="list">
            {results?.competencies.map((competency) => (
              <div className="item" key={competency.competency_id}>
                <strong>{competency.competency_name}</strong>
                <span className="muted">
                  Promedio {competency.average} | Mediana {competency.median} | Desvio {competency.stddev}
                </span>
              </div>
            ))}
            {results?.ranking.map((row) => (
              <div className="item" key={row.participant_id}>
                <strong>
                  #{row.rank} {row.participant_name}
                </strong>
                <span className="muted">Promedio {row.average}</span>
              </div>
            ))}
            {!results?.competencies.length && <p className="muted">Todavia no hay respuestas.</p>}
          </div>
        </section>
      </section>
    </main>
  );
}
