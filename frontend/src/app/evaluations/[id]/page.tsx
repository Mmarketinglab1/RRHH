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
  API_URL,
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
  const [activeTab, setActiveTab] = useState<'structure' | 'participants' | 'results'>('structure');
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
    const qType = String(data.get("question_type") || "numeric_1_10");
    const rawOpts = String(data.get("options_raw") || "");
    const isEvaluative = data.get("is_evaluative") === "true";

    let parsedOptions: any = null;
    if (qType === "semantic_differential") {
      const parts = rawOpts.split(/[-,\r\n]+/).map(p => p.trim()).filter(Boolean);
      if (parts.length === 2) {
        parsedOptions = { left_label: parts[0], right_label: parts[1], steps: 7 };
      } else {
        parsedOptions = { left_label: "Muy malo", right_label: "Muy bueno", steps: 7 };
      }
    } else if (qType !== "numeric_1_10" && qType !== "nps" && qType !== "dicotomic" && rawOpts) {
      parsedOptions = rawOpts.split(",").map(o => o.trim()).filter(Boolean);
    }

    await postForm<Question>(`/evaluations/${evaluationId}/questions`, event, {
      competency_id: data.get("competency_id"),
      text: data.get("text"),
      position: Number(data.get("position") || questions.length + 1),
      question_type: qType,
      options: parsedOptions,
      is_evaluative: isEvaluative,
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
      const fullUrl = `${window.location.origin}${result.public_url.replace("/surveys/public", "/survey")}`;
      try {
        await navigator.clipboard.writeText(fullUrl);
        setMessage(`Link copiado al portapapeles: ${fullUrl}`);
      } catch {
        setMessage(`Link publico (selecciona para copiar): ${fullUrl}`);
      }
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

  async function handleDownloadTemplate() {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/evaluations/${evaluationId}/competencies/import-template`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        throw new Error("No se pudo descargar la plantilla");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "plantilla_competencias.xlsx";
      document.body.appendChild(a);
      a.click();
      a.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Error al descargar plantilla");
    } finally {
      setLoading(false);
    }
  }

  async function handleExcelUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !token) return;

    setLoading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/evaluations/${evaluationId}/competencies/import`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        let errorMsg = "Error al importar el archivo";
        try {
          const errData = await response.json();
          errorMsg = errData.detail || errorMsg;
        } catch {
          // Ignore
        }
        throw new Error(errorMsg);
      }

      const result = await response.json();
      setMessage(
        `Importación completa: se crearon ${result.competencies_created} competencias y ${result.questions_created} preguntas (${result.questions_skipped} preguntas duplicadas omitidas).`
      );
      
      event.target.value = "";
      await refreshAll(token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Error al importar Excel");
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
    const qType = String(data.get("question_type") || "numeric_1_10");
    const rawOpts = String(data.get("options_raw") || "");
    const isEvaluative = data.get("is_evaluative") === "true";

    let parsedOptions: any = null;
    if (qType === "semantic_differential") {
      const parts = rawOpts.split(/[-,\r\n]+/).map(p => p.trim()).filter(Boolean);
      if (parts.length === 2) {
        parsedOptions = { left_label: parts[0], right_label: parts[1], steps: 7 };
      } else {
        parsedOptions = { left_label: "Muy malo", right_label: "Muy bueno", steps: 7 };
      }
    } else if (qType !== "numeric_1_10" && qType !== "nps" && qType !== "dicotomic" && rawOpts) {
      parsedOptions = rawOpts.split(",").map(o => o.trim()).filter(Boolean);
    }

    const updated = await patchResource<Question>(
      `/evaluations/${evaluationId}/questions/${questionId}`,
      {
        competency_id: data.get("competency_id"),
        text: data.get("text"),
        position: Number(data.get("position") || 0),
        question_type: qType,
        options: parsedOptions,
        is_evaluative: isEvaluative,
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

        <div className="page-tabs">
          <button
            className={`page-tab ${activeTab === "structure" ? "active" : ""}`}
            onClick={() => setActiveTab("structure")}
            type="button"
          >
            Estructura del Formulario
          </button>
          <button
            className={`page-tab ${activeTab === "participants" ? "active" : ""}`}
            onClick={() => setActiveTab("participants")}
            type="button"
          >
            Participantes y Relaciones
          </button>
          <button
            className={`page-tab ${activeTab === "results" ? "active" : ""}`}
            onClick={() => setActiveTab("results")}
            type="button"
          >
            Resultados
          </button>
        </div>

        {activeTab === "structure" && (
          <div className="grid two">
            <section className="panel">
              <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
                <h2>Competencias</h2>
                <div className="toolbar" style={{ gap: 8 }}>
                  <button
                    type="button"
                    className="button secondary"
                    onClick={handleDownloadTemplate}
                    disabled={loading}
                    style={{ fontSize: "0.8rem", padding: "6px 10px" }}
                  >
                    Descargar Plantilla
                  </button>
                  <label
                    className="button secondary"
                    style={{ fontSize: "0.8rem", padding: "6px 10px", cursor: "pointer", margin: 0 }}
                  >
                    Importar Excel
                    <input
                      type="file"
                      accept=".xlsx"
                      style={{ display: "none" }}
                      onChange={handleExcelUpload}
                      disabled={loading}
                    />
                  </label>
                </div>
              </div>
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
                <div className="field">
                  <label>Tipo de Pregunta</label>
                  <select className="select" defaultValue="numeric_1_10" name="question_type" required>
                    <option value="numeric_1_10">Escala Numérica (1-10)</option>
                    <option value="nps">NPS (Net Promoter Score 0-10)</option>
                    <option value="dicotomic">Dicotómica (Sí/No)</option>
                    <option value="likert">Escala Likert (5 opciones estándar)</option>
                    <option value="single_choice">Opción Múltiple (Única)</option>
                    <option value="multiple_choice">Opción Múltiple (Múltiple)</option>
                    <option value="semantic_differential">Diferencial Semántico (Malo - Bueno)</option>
                    <option value="ranking">Ordenamiento / Ranking</option>
                    <option value="checklist">Checklist (Lista verificación)</option>
                    <option value="frequency">Frecuencia (Nunca, A veces...)</option>
                    <option value="categorization">Categorización (Rango etario...)</option>
                  </select>
                </div>
                <div className="field">
                  <label>Opciones (separadas por coma; ej: Aceptable, Bueno, Excelente. Para diferencial: "Malo - Bueno")</label>
                  <input className="input" name="options_raw" placeholder="Opción A, Opción B, Opción C" />
                </div>
                <div className="field" style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 12 }}>
                  <select className="select" defaultValue="true" name="is_evaluative" style={{ width: "auto", minHeight: 34, padding: "4px 8px" }}>
                    <option value="true">Sí (Evaluativa - suma al promedio de competencia)</option>
                    <option value="false">No (Informativa / Cualitativa únicamente)</option>
                  </select>
                </div>
                <input name="position" type="hidden" value={questions.length + 1} />
                <button className="button" disabled={loading || !competencies.length} type="submit" style={{ marginTop: 8 }}>
                  <Plus size={16} />
                  Agregar Pregunta
                </button>
              </form>
              <div className="list">
                {questions.map((question) => (
                  <div className="item" key={question.id} style={{ display: "block" }}>
                    {editingQuestionId === question.id ? (
                      <form className="form" onSubmit={(event) => updateQuestion(event, question.id)}>
                        <div className="field">
                          <label>Competencia</label>
                          <select className="select" defaultValue={question.competency_id} name="competency_id" required>
                            {competencies.map((competency) => (
                              <option key={competency.id} value={competency.id}>
                                {competency.name}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="field">
                          <label>Pregunta</label>
                          <textarea className="textarea" defaultValue={question.text} name="text" required />
                        </div>
                        <div className="field">
                          <label>Tipo</label>
                          <select className="select" defaultValue={question.question_type || "numeric_1_10"} name="question_type" required>
                            <option value="numeric_1_10">Escala Numérica (1-10)</option>
                            <option value="nps">NPS (Net Promoter Score 0-10)</option>
                            <option value="dicotomic">Dicotómica (Sí/No)</option>
                            <option value="likert">Escala Likert (5 opciones estándar)</option>
                            <option value="single_choice">Opción Múltiple (Única)</option>
                            <option value="multiple_choice">Opción Múltiple (Múltiple)</option>
                            <option value="semantic_differential">Diferencial Semántico (Malo - Bueno)</option>
                            <option value="ranking">Ordenamiento / Ranking</option>
                            <option value="checklist">Checklist (Lista verificación)</option>
                            <option value="frequency">Frecuencia (Nunca, A veces...)</option>
                            <option value="categorization">Categorización (Rango etario...)</option>
                          </select>
                        </div>
                        <div className="field">
                          <label>Opciones (separadas por coma)</label>
                          <input
                            className="input"
                            defaultValue={
                              question.options
                                ? Array.isArray(question.options)
                                  ? question.options.join(", ")
                                  : typeof question.options === "object"
                                  ? `${question.options.left_label} - ${question.options.right_label}`
                                  : String(question.options)
                                : ""
                            }
                            name="options_raw"
                          />
                        </div>
                        <div className="field">
                          <label>Uso Estadístico</label>
                          <select className="select" defaultValue={String(question.is_evaluative ?? true)} name="is_evaluative">
                            <option value="true">Sí (Evaluativa - suma al promedio)</option>
                            <option value="false">No (Informativa - no suma al promedio)</option>
                          </select>
                        </div>
                        <div className="field">
                          <label>Posición</label>
                          <input className="input" defaultValue={question.position} name="position" type="number" />
                        </div>
                        <div className="toolbar" style={{ marginTop: 12 }}>
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
                        <div className="row" style={{ marginTop: 6, gap: 8, justifyContent: "flex-start", flexWrap: "wrap" }}>
                          <span className="status-pill" style={{ fontSize: "0.75rem", padding: "2px 6px" }}>{question.question_type || "numeric_1_10"}</span>
                          {question.is_evaluative ? (
                            <span className="status-pill" style={{ fontSize: "0.75rem", padding: "2px 6px", background: "var(--accent-soft)", color: "var(--accent-dark)", border: "1px solid #b8ddd6" }}>Evaluativa</span>
                          ) : (
                            <span className="status-pill" style={{ fontSize: "0.75rem", padding: "2px 6px", background: "#edf1f6", color: "#263244", border: "1px solid var(--line)" }}>Informativa</span>
                          )}
                          <span className="muted" style={{ fontSize: "0.8rem" }}>Posición: {question.position}</span>
                        </div>
                        {question.options && (
                          <span className="muted" style={{ display: "block", fontSize: "0.8rem", marginTop: 6, background: "rgba(0,0,0,0.02)", padding: "4px 8px", borderRadius: 4 }}>
                            Opciones: {
                              Array.isArray(question.options)
                                ? question.options.join(", ")
                                : typeof question.options === "object"
                                ? `${question.options.left_label} ↔ ${question.options.right_label} (${question.options.steps || 7} pasos)`
                                : JSON.stringify(question.options)
                            }
                          </span>
                        )}
                        <div className="toolbar" style={{ marginTop: 10 }}>
                          <button className="button secondary" onClick={() => setEditingQuestionId(question.id)} type="button" style={{ minHeight: 32, height: 32, padding: "4px 10px", fontSize: "0.8rem" }}>
                            <Pencil size={12} />
                            Editar
                          </button>
                          <button
                            className="button danger"
                            onClick={() => deleteResource(`/evaluations/${evaluationId}/questions/${question.id}`, "pregunta")}
                            type="button"
                            style={{ minHeight: 32, height: 32, padding: "4px 10px", fontSize: "0.8rem" }}
                          >
                            <Trash2 size={12} />
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
          </div>
        )}

        {activeTab === "participants" && (
          <div className="grid two">
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
        )}

        {activeTab === "results" && (
          <>
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

            <div className="grid two" style={{ marginTop: 18 }}>
              <section className="panel">
                <h2>Promedios por Competencia</h2>
                <div className="list">
                  {results?.competencies.map((competency) => (
                    <div className="item" key={competency.competency_id}>
                      <div className="row">
                        <strong>{competency.competency_name}</strong>
                        <span className="status-pill" style={{ background: "var(--accent-soft)", color: "var(--accent-dark)" }}>Promedio: {competency.average}</span>
                      </div>
                      <span className="muted" style={{ fontSize: "0.85rem" }}>
                        Mediana: {competency.median} | Desvío: {competency.stddev} | Respuestas: {competency.responses}
                      </span>
                    </div>
                  ))}
                  {!results?.competencies.length && <p className="muted">No hay respuestas cargadas aún.</p>}
                </div>
              </section>

              <section className="panel">
                <h2>Ranking de Participantes</h2>
                <div className="list">
                  {results?.ranking.map((row) => (
                    <div className="item" key={row.participant_id}>
                      <div className="row">
                        <strong>
                          #{row.rank} {row.participant_name}
                        </strong>
                        <span className="status-pill" style={{ background: "var(--accent)", color: "#fff" }}>Score: {row.average}</span>
                      </div>
                    </div>
                  ))}
                  {!results?.ranking.length && <p className="muted">No hay rankings disponibles.</p>}
                </div>
              </section>
            </div>

            <section className="panel" style={{ marginTop: 18 }}>
              <h2>Desglose Estadístico por Pregunta</h2>
              <div className="list">
                {results?.questions?.map((q) => {
                  const distributionEntries = Object.entries(q.distribution || {});
                  const totalAnswers = distributionEntries.reduce((a, b) => a + b[1], 0);
                  
                  // Calculate NPS score if question type is nps
                  let npsScore: number | null = null;
                  if (q.question_type === "nps" && totalAnswers > 0) {
                    const promoters = q.distribution["Promotores (9-10)"] || 0;
                    const detractors = q.distribution["Detractores (0-6)"] || 0;
                    npsScore = Math.round(((promoters - detractors) / totalAnswers) * 100);
                  }

                  return (
                    <div className="item" key={q.question_id} style={{ display: "block" }}>
                      <div className="row" style={{ alignItems: "flex-start", marginBottom: 8 }}>
                        <div>
                          <span className="status-pill" style={{ marginRight: 6, fontSize: "0.75rem", padding: "2px 6px" }}>{q.competency_name}</span>
                          <span className="status-pill" style={{ marginRight: 6, fontSize: "0.75rem", padding: "2px 6px" }}>{q.question_type}</span>
                          {q.is_evaluative ? (
                            <span className="status-pill" style={{ marginRight: 6, fontSize: "0.75rem", padding: "2px 6px", background: "var(--accent-soft)", color: "var(--accent-dark)", border: "1px solid #b8ddd6" }}>Evaluativa</span>
                          ) : (
                            <span className="status-pill" style={{ marginRight: 6, fontSize: "0.75rem", padding: "2px 6px", background: "#edf1f6", color: "#263244" }}>Informativa</span>
                          )}
                          <h4 style={{ marginTop: 8, fontSize: "1.05rem", fontWeight: 700 }}>{q.question_text}</h4>
                        </div>
                        {q.is_evaluative && q.average !== null && (
                          <div style={{ textAlign: "right", minWidth: 80 }}>
                            <div style={{ fontSize: "1.3rem", fontWeight: "bold", color: "var(--accent-dark)" }}>
                              {q.average}
                            </div>
                            <span className="muted" style={{ fontSize: "0.75rem" }}>Promedio</span>
                          </div>
                        )}
                        {q.question_type === "nps" && npsScore !== null && (
                          <div style={{ textAlign: "right", minWidth: 80, marginLeft: 12 }}>
                            <div style={{ fontSize: "1.3rem", fontWeight: "bold", color: npsScore >= 30 ? "var(--accent)" : npsScore >= 0 ? "orange" : "var(--danger)" }}>
                              {npsScore > 0 ? `+${npsScore}` : npsScore}
                            </div>
                            <span className="muted" style={{ fontSize: "0.75rem" }}>NPS Score</span>
                          </div>
                        )}
                      </div>

                      {q.is_evaluative && q.average !== null && (
                        <p className="muted" style={{ fontSize: "0.8rem", marginBottom: 12 }}>
                          Mediana: {q.median} | Desvío: {q.stddev} | Respuestas: {q.responses_count}
                        </p>
                      )}

                      <div style={{ marginTop: 12, background: "rgba(0,0,0,0.012)", padding: 12, borderRadius: 6, border: "1px solid var(--line)" }}>
                        <span className="muted" style={{ fontSize: "0.75rem", display: "block", marginBottom: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                          Distribución de Respuestas ({totalAnswers} en total):
                        </span>
                        {distributionEntries.map(([opt, count]) => {
                          const percentage = totalAnswers > 0 ? Math.round((count / totalAnswers) * 100) : 0;
                          return (
                            <div key={opt} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                              <span style={{ width: 160, fontSize: "0.8rem", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }} title={opt}>
                                {opt}
                              </span>
                              <div style={{ flex: 1, height: 12, background: "rgba(0,0,0,0.05)", borderRadius: 6, overflow: "hidden" }}>
                                <div style={{ width: `${percentage}%`, height: "100%", background: "var(--accent)", borderRadius: 6, transition: "width 0.4s ease" }} />
                              </div>
                              <span style={{ width: 90, fontSize: "0.8rem", fontWeight: "bold", textAlign: "right" }}>
                                {percentage}% ({count})
                              </span>
                            </div>
                          );
                        })}
                        {totalAnswers === 0 && <p className="muted" style={{ fontSize: "0.8rem" }}>Sin respuestas registradas.</p>}
                      </div>
                    </div>
                  );
                })}
                {!results?.questions?.length && <p className="muted">No hay estadísticas de preguntas cargadas.</p>}
              </div>
            </section>
          </>
        )}
      </section>
    </main>
  );
}
