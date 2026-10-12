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
  Copy,
  Check,
  ExternalLink,
  Search,
  ChevronDown,
  ChevronUp,
  LayoutGrid,
  Table,
  Download,
  FileText,
  FileArchive,
  Settings,
  Upload,
  Image as ImageIcon,
  Sliders,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, Fragment, useEffect, useMemo, useState } from "react";
import {
  api,
  API_URL,
  downloadFile,
  Assignment,
  Competency,
  CompetencyBank,
  Evaluation,
  EvaluationResults,
  ExecutiveReportResults,
  Participant,
  ParticipantDetailResults,
  Question,
} from "@/lib/api";


// Banco de preguntas sugeridas migrado a base de datos de manera dinámica

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
  const [activeTab, setActiveTab] = useState<'structure' | 'participants' | 'dispatch' | 'results'>('structure');
  const [dispatchSearch, setDispatchSearch] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
  const [expandedEvaluatees, setExpandedEvaluatees] = useState<Record<string, boolean>>({});
  const [editingCompetencyId, setEditingCompetencyId] = useState<string | null>(null);
  const [editingQuestionId, setEditingQuestionId] = useState<string | null>(null);
  const [editingParticipantId, setEditingParticipantId] = useState<string | null>(null);
  
  const [selectedCompForSuggestion, setSelectedCompForSuggestion] = useState<string>("");
  const [selectedPresetQuestions, setSelectedPresetQuestions] = useState<string[]>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<any[]>([]);

  const [competencyBankOptions, setCompetencyBankOptions] = useState<CompetencyBank[]>([]);
  const [isCustomCompetency, setIsCustomCompetency] = useState<boolean>(false);
  const [prefilledDesc, setPrefilledDesc] = useState<string>("");
  
  const [selectedEvaluateeId, setSelectedEvaluateeId] = useState<string>("");

  const [resultsSubTab, setResultsSubTab] = useState<'general' | 'participant' | 'executive'>('general');
  const [selectedParticipantForReport, setSelectedParticipantForReport] = useState<string>("");
  const [participantReport, setParticipantReport] = useState<ParticipantDetailResults | null>(null);
  const [loadingParticipantReport, setLoadingParticipantReport] = useState(false);
  const [downloadingGeneralPdf, setDownloadingGeneralPdf] = useState(false);
  const [downloadingParticipantPdf, setDownloadingParticipantPdf] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);
  const [downloadingExecutivePdf, setDownloadingExecutivePdf] = useState(false);
  const [executiveResults, setExecutiveResults] = useState<ExecutiveReportResults | null>(null);
  const [loadingExecutive, setLoadingExecutive] = useState(false);

  const [showReportConfigModal, setShowReportConfigModal] = useState(false);
  const [savingReportConfig, setSavingReportConfig] = useState(false);
  const [configTab, setConfigTab] = useState<'branding' | 'content' | 'thresholds' | 'display'>('branding');

  const [clientLogoUrl, setClientLogoUrl] = useState<string>("");
  const [consultantLogoUrl, setConsultantLogoUrl] = useState<string>("");
  const [thHigh, setThHigh] = useState<number>(8.5);
  const [thMed, setThMed] = useState<number>(7.0);
  const [companyName, setCompanyName] = useState<string>("MSD");
  const [consultantName, setConsultantName] = useState<string>("abc&co");
  const [coverTitle1, setCoverTitle1] = useState<string>("REPORTE DE");
  const [coverTitle2, setCoverTitle2] = useState<string>("EVALUACIÓN");
  const [coverTitle3, setCoverTitle3] = useState<string>("360°");
  const [coverSub1, setCoverSub1] = useState<string>("REPORTE GRUPAL");
  const [coverSub2, setCoverSub2] = useState<string>("Fuerza de ventas");
  const [headerTitle, setHeaderTitle] = useState<string>("Reporte Grupal - Evaluación 360°");
  const [introP1, setIntroP1] = useState<string>("");
  const [introP2, setIntroP2] = useState<string>("");
  const [objectivesMain, setObjectivesMain] = useState<string>("");
  const [labelHigh, setLabelHigh] = useState<string>("Excede expectativas");
  const [labelMed, setLabelMed] = useState<string>("Cumple expectativas");
  const [labelLow, setLabelLow] = useState<string>("Necesita mejora");
  const [showPicosAlert, setShowPicosAlert] = useState<boolean>(true);
  const [showInsightsSection, setShowInsightsSection] = useState<boolean>(true);
  const [showRankingTable, setShowRankingTable] = useState<boolean>(true);

  useEffect(() => {
    if (evaluation) {
      setClientLogoUrl(evaluation.client_logo_url || "");
      setConsultantLogoUrl(evaluation.consultant_logo_url || "");
      if (evaluation.score_thresholds) {
        setThHigh(Number(evaluation.score_thresholds.high) || 8.5);
        setThMed(Number(evaluation.score_thresholds.medium) || 7.0);
      }
      const cfg = evaluation.report_config || {};
      setCompanyName(cfg.company_name || evaluation.title || "MSD");
      setConsultantName(cfg.consultant_name || "abc&co");
      setCoverTitle1(cfg.cover_title_1 || "REPORTE DE");
      setCoverTitle2(cfg.cover_title_2 || "EVALUACIÓN");
      setCoverTitle3(cfg.cover_title_3 || "360°");
      setCoverSub1(cfg.cover_subtitle_1 || "REPORTE GRUPAL");
      setCoverSub2(cfg.cover_subtitle_2 || `Fuerza de ventas ${cfg.company_name || evaluation.title || "MSD"}`);
      setHeaderTitle(cfg.header_title || "Reporte Grupal - Evaluación 360°");
      setIntroP1(cfg.intro_p1 || "");
      setIntroP2(cfg.intro_p2 || "");
      setObjectivesMain(cfg.objectives_main || "");
      setLabelHigh(cfg.label_high || "Excede expectativas");
      setLabelMed(cfg.label_med || "Cumple expectativas");
      setLabelLow(cfg.label_low || "Necesita mejora");
      if (cfg.show_picos_alert !== undefined) setShowPicosAlert(cfg.show_picos_alert);
      if (cfg.show_insights_section !== undefined) setShowInsightsSection(cfg.show_insights_section);
      if (cfg.show_ranking_table !== undefined) setShowRankingTable(cfg.show_ranking_table);
    }
  }, [evaluation]);

  function handleLogoFileUpload(e: React.ChangeEvent<HTMLInputElement>, target: 'client' | 'consultant') {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      alert("La imagen no debe superar los 5MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      if (target === 'client') {
        setClientLogoUrl(result);
      } else {
        setConsultantLogoUrl(result);
      }
    };
    reader.readAsDataURL(file);
  }

  async function handleSaveReportConfig() {
    if (!token || !evaluationId) return;
    setSavingReportConfig(true);
    try {
      const payload = {
        client_logo_url: clientLogoUrl || null,
        consultant_logo_url: consultantLogoUrl || null,
        score_thresholds: {
          high: Number(thHigh) || 8.5,
          medium: Number(thMed) || 7.0,
        },
        report_config: {
          company_name: companyName,
          consultant_name: consultantName,
          cover_title_1: coverTitle1,
          cover_title_2: coverTitle2,
          cover_title_3: coverTitle3,
          cover_subtitle_1: coverSub1,
          cover_subtitle_2: coverSub2,
          header_title: headerTitle,
          intro_p1: introP1,
          intro_p2: introP2,
          objectives_main: objectivesMain,
          label_high: labelHigh,
          label_med: labelMed,
          label_low: labelLow,
          show_picos_alert: showPicosAlert,
          show_insights_section: showInsightsSection,
          show_ranking_table: showRankingTable,
        },
      };

      const updated = await api<Evaluation>(
        `/evaluations/${evaluationId}`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        },
        token
      );
      setEvaluation(updated);
      setShowReportConfigModal(false);
      setMessage("Configuración del informe guardada correctamente.");
      await loadExecutiveReport(token);
    } catch (err: any) {
      alert(`Error al guardar configuración: ${err.message}`);
    } finally {
      setSavingReportConfig(false);
    }
  }

  async function handleDownloadGeneralPdf() {
    if (!token || !evaluationId) return;
    setDownloadingGeneralPdf(true);
    try {
      await downloadFile(`/evaluations/${evaluationId}/results/pdf`, `Informe_General_360.pdf`, token);
    } catch (err: any) {
      setMessage(`Error al descargar PDF General: ${err.message}`);
    } finally {
      setDownloadingGeneralPdf(false);
    }
  }

  async function handleDownloadExecutivePdf() {
    if (!token || !evaluationId) return;
    setDownloadingExecutivePdf(true);
    try {
      await downloadFile(
        `/evaluations/${evaluationId}/results/executive/pdf`,
        `Reporte_Ejecutivo_360_${evaluation?.title?.replace(/\s+/g, "_") || "MSD"}.pdf`,
        token
      );
    } catch (err: any) {
      setMessage(`Error al descargar Reporte Ejecutivo (29 Páginas): ${err.message}`);
    } finally {
      setDownloadingExecutivePdf(false);
    }
  }

  async function loadExecutiveReport(authToken = token) {
    if (!authToken || !evaluationId) return;
    setLoadingExecutive(true);
    try {
      const data = await api<ExecutiveReportResults>(
        `/evaluations/${evaluationId}/results/executive`,
        {},
        authToken
      );
      setExecutiveResults(data);
    } catch (err: any) {
      setMessage(`Error al cargar datos del reporte ejecutivo: ${err.message}`);
    } finally {
      setLoadingExecutive(false);
    }
  }

  async function handleDownloadParticipantPdf(participantId: string) {
    if (!token || !evaluationId || !participantId) return;
    setDownloadingParticipantPdf(true);
    try {
      await downloadFile(
        `/evaluations/${evaluationId}/results/participant/${participantId}/pdf`,
        `Informe_Individual_360.pdf`,
        token
      );
    } catch (err: any) {
      setMessage(`Error al descargar PDF Individual: ${err.message}`);
    } finally {
      setDownloadingParticipantPdf(false);
    }
  }

  async function handleDownloadZip() {
    if (!token || !evaluationId) return;
    setDownloadingZip(true);
    try {
      await downloadFile(
        `/evaluations/${evaluationId}/results/participants/pdf-zip`,
        `Informes_Todos_Colaboradores.zip`,
        token
      );
    } catch (err: any) {
      setMessage(`Error al descargar ZIP Masivo: ${err.message}`);
    } finally {
      setDownloadingZip(false);
    }
  }


  const firstCompetency = competencies[0]?.id || "";

  async function loadParticipantReport(participantId: string, authToken = token) {
    if (!authToken || !participantId) return;
    setLoadingParticipantReport(true);
    try {
      const data = await api<ParticipantDetailResults>(
        `/evaluations/${evaluationId}/results/participant/${participantId}`,
        {},
        authToken
      );
      setParticipantReport(data);
    } catch {
      setParticipantReport(null);
    } finally {
      setLoadingParticipantReport(false);
    }
  }

  useEffect(() => {
    if (token && selectedParticipantForReport) {
      void loadParticipantReport(selectedParticipantForReport, token);
    }
  }, [token, selectedParticipantForReport]);

  useEffect(() => {
    if (resultsSubTab === "participant" && participants.length > 0 && !selectedParticipantForReport) {
      setSelectedParticipantForReport(participants[0].id);
    }
  }, [resultsSubTab, participants, selectedParticipantForReport]);

  async function loadSuggestedQuestions(competencyId: string, authToken = token) {
    if (!authToken || !competencyId) return;
    try {
      const data = await api<any[]>(`/evaluations/${evaluationId}/suggested-questions?competency_id=${competencyId}`, {}, authToken);
      setSuggestedQuestions(data);
    } catch {
      setSuggestedQuestions([]);
    }
  }

  useEffect(() => {
    if (token && selectedCompForSuggestion) {
      void loadSuggestedQuestions(selectedCompForSuggestion, token);
    }
  }, [token, selectedCompForSuggestion]);

  useEffect(() => {
    const saved = localStorage.getItem("rrhh_token");
    setToken(saved);
  }, []);

  useEffect(() => {
    setSelectedCompForSuggestion("");
    setSuggestedQuestions([]);
    setSelectedPresetQuestions([]);
    setEditingCompetencyId(null);
    setEditingQuestionId(null);
    setEditingParticipantId(null);
    setResults(null);
  }, [evaluationId]);

  useEffect(() => {
    if (competencies.length > 0 && !selectedCompForSuggestion) {
      setSelectedCompForSuggestion(competencies[0].id);
    }
  }, [competencies, selectedCompForSuggestion]);

  useEffect(() => {
    if (token && evaluationId) {
      void refreshAll(token);
    }
  }, [token, evaluationId]);

  useEffect(() => {
    if (participants.length > 0) {
      if (!selectedEvaluateeId || !participants.some(p => p.id === selectedEvaluateeId)) {
        setSelectedEvaluateeId(participants[0].id);
      }
    } else {
      setSelectedEvaluateeId("");
    }
  }, [participants, selectedEvaluateeId]);

  async function refreshAll(authToken = token) {
    if (!authToken) return;
    setLoading(true);
    setMessage("");
    try {
      const [evaluationData, competencyData, questionData, participantData, assignmentData, bankData] = await Promise.all([
        api<Evaluation>(`/evaluations/${evaluationId}`, {}, authToken),
        api<Competency[]>(`/evaluations/${evaluationId}/competencies`, {}, authToken),
        api<Question[]>(`/evaluations/${evaluationId}/questions`, {}, authToken),
        api<Participant[]>(`/evaluations/${evaluationId}/participants`, {}, authToken),
        api<Assignment[]>(`/evaluations/${evaluationId}/assignments`, {}, authToken),
        api<CompetencyBank[]>("/competency-bank", {}, authToken),
      ]);
      setEvaluation(evaluationData);
      setCompetencies(competencyData);
      setQuestions(questionData);
      setParticipants(participantData);
      setAssignments(assignmentData);
      setCompetencyBankOptions(bankData);
      await loadResults(authToken);

      const activeCompId = selectedCompForSuggestion || competencyData[0]?.id;
      if (activeCompId) {
        await loadSuggestedQuestions(activeCompId, authToken);
      }
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

  async function handleStatusChange(newStatus: string) {
    if (!token || !evaluation) return;
    setLoading(true);
    setMessage("");
    try {
      const updated = await api<Evaluation>(
        `/evaluations/${evaluationId}`,
        {
          method: "PATCH",
          body: JSON.stringify({ status: newStatus }),
        },
        token
      );
      setEvaluation(updated);
      setMessage("Estado de la evaluación actualizado correctamente.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo actualizar el estado");
    } finally {
      setLoading(false);
    }
  }

  async function handleAssessmentTypeChange(newType: string) {
    if (!token || !evaluation) return;
    setLoading(true);
    setMessage("");
    try {
      const updated = await api<Evaluation>(
        `/evaluations/${evaluationId}`,
        {
          method: "PATCH",
          body: JSON.stringify({ assessment_type: newType }),
        },
        token
      );
      setEvaluation(updated);
      setMessage("Tipo de assessment actualizado correctamente.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo actualizar el tipo de assessment");
    } finally {
      setLoading(false);
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
    const bankSelectVal = String(data.get("competency_bank_select") || "");
    
    let compName = "";
    let compBankId: string | null = null;
    
    if (bankSelectVal === "custom") {
      compName = String(data.get("custom_name") || "").trim();
    } else {
      const selectedBank = competencyBankOptions.find(b => b.id === bankSelectVal);
      if (selectedBank) {
        compName = selectedBank.name;
        compBankId = selectedBank.id;
      }
    }
    
    if (!compName) {
      setMessage("Por favor selecciona o escribe una competencia válida.");
      event.preventDefault();
      return;
    }

    const res = await postForm<Competency>(`/evaluations/${evaluationId}/competencies`, event, {
      name: compName,
      competency_bank_id: compBankId,
      description: data.get("description"),
      weight: Number(data.get("weight") || 100) / 100,
    });

    if (res) {
      setIsCustomCompetency(false);
      setPrefilledDesc("");
    }
  }

  async function addQuestion(event: FormEvent<HTMLFormElement>) {
    const data = new FormData(event.currentTarget);
    const qType = String(data.get("question_type") || "numeric_1_10");
    const rawOpts = String(data.get("options_raw") || "");
    const isEvaluative = data.get("is_evaluative") === "true";
    const saveToBank = data.get("save_to_bank") === "true";
    const competencyId = String(data.get("competency_id") || "");
    const textSelf = String(data.get("text_self") || "");

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

    const res = await postForm<Question>(`/evaluations/${evaluationId}/questions`, event, {
      competency_id: competencyId,
      text: textSelf,
      text_self: textSelf,
      text_evaluator: String(data.get("text_evaluator") || textSelf),
      tag_self: String(data.get("tag_self") || ""),
      tag_evaluator: String(data.get("tag_evaluator") || ""),
      position: Number(data.get("position") || questions.length + 1),
      question_type: qType,
      options: parsedOptions,
      is_evaluative: isEvaluative,
      save_to_bank: saveToBank,
    });

    if (res && competencyId) {
      void loadSuggestedQuestions(competencyId);
    }
  }

  async function addPresetQuestions(selectedPresets: any[], targetCompetencyId: string) {
    if (!token || selectedPresets.length === 0) return;
    setLoading(true);
    setMessage("");
    try {
      let index = 0;
      for (const preset of selectedPresets) {
        await api(`/evaluations/${evaluationId}/questions`, {
          method: "POST",
          body: JSON.stringify({
            competency_id: targetCompetencyId,
            text: preset.text,
            text_self: preset.text_self || preset.text,
            text_evaluator: preset.text_evaluator || preset.text,
            tag_self: preset.tag_self || `P${questions.length + index + 1} Autoevaluado`,
            tag_evaluator: preset.tag_evaluator || `P${questions.length + index + 1}B Evaluador`,
            position: questions.length + index + 1,
            question_type: preset.question_type || "numeric_1_10",
            options: preset.options || null,
            is_evaluative: preset.is_evaluative !== undefined ? preset.is_evaluative : true,
          }),
        }, token);
        index++;
      }
      setMessage(`Se agregaron ${selectedPresets.length} preguntas sugeridas.`);
      await refreshAll(token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Error al agregar preguntas");
    } finally {
      setLoading(false);
    }
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
    await postForm<Assignment>(`/evaluations/${evaluationId}/assignments`, event, {
      evaluatee_id: data.get("evaluatee_id"),
      evaluator_id: data.get("evaluator_id"),
      relationship: data.get("relationship") || "peer",
      weight: Number(data.get("weight") || 100) / 100,
    });
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
    
    let confirmMsg = `¿Eliminar ${label}? Esta acción no se puede deshacer.`;
    if (label === "pregunta") {
      confirmMsg = "¿Eliminar esta pregunta? Se borrarán de forma permanente todas las respuestas de encuestas y las estadísticas asociadas a esta pregunta. Esta acción no se puede deshacer.";
    } else if (label === "competencia") {
      confirmMsg = "¿Eliminar esta competencia? Se borrarán de forma permanente todas sus preguntas asociadas, respuestas de encuestas y estadísticas. Esta acción no se puede deshacer.";
    } else if (label === "participante") {
      confirmMsg = "¿Eliminar este participante? Se borrarán de forma permanente todas sus autoevaluaciones, relaciones de evaluadores y respuestas enviadas. Esta acción no se puede deshacer.";
    }

    if (!window.confirm(confirmMsg)) return;
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
      document.body.removeChild(a);
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

  async function handleDownloadParticipantsTemplate() {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/evaluations/${evaluationId}/participants/import-template`, {
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
      a.download = "plantilla_participantes.xlsx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Error al descargar plantilla");
    } finally {
      setLoading(false);
    }
  }

  async function handleParticipantsExcelUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !token) return;

    setLoading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/evaluations/${evaluationId}/participants/import`, {
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
        `Importación completa: se crearon ${result.participants_created} participantes y ${result.assignments_created} asignaciones de relaciones.`
      );
      
      event.target.value = "";
      await refreshAll(token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Error al importar Excel");
    } finally {
      setLoading(false);
    }
  }

  async function handleExportLinks() {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(
        `${API_URL}/evaluations/${evaluationId}/assignments/export-links?frontend_url=${encodeURIComponent(window.location.origin)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (!response.ok) {
        throw new Error("No se pudieron exportar los links de las encuestas");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `links_encuestas_${evaluationId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setMessage("Se exportaron los links de las encuestas en Excel.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Error al exportar links");
    } finally {
      setLoading(false);
    }
  }

  function handleCopy(text: string, id: string) {
    void navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => {
      setCopiedId((current) => (current === id ? null : current));
    }, 2000);
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
        weight: Number(data.get("weight") || 100) / 100,
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
    const textSelf = String(data.get("text_self") || "");

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
        text: textSelf,
        text_self: textSelf,
        text_evaluator: String(data.get("text_evaluator") || textSelf),
        tag_self: String(data.get("tag_self") || ""),
        tag_evaluator: String(data.get("tag_evaluator") || ""),
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

  const sortedAssignments = useMemo(() => {
    return [...assignments]
      .filter((a) => a.relationship !== "self")
      .map((assignment) => {
        const evaluatee = participants.find((p) => p.id === assignment.evaluatee_id);
        const evaluator = participants.find((p) => p.id === assignment.evaluator_id);
        return {
          ...assignment,
          evaluateeName: evaluatee ? evaluatee.full_name : "Desconocido",
          evaluatorName: evaluator ? evaluator.full_name : "Desconocido",
        };
      }).sort((a, b) => {
        const cmp = a.evaluateeName.localeCompare(b.evaluateeName);
        if (cmp !== 0) return cmp;
        return a.evaluatorName.localeCompare(b.evaluatorName);
      });
  }, [assignments, participants]);

  async function handleSeedDemo() {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      const res = await api<{ message: string }>(`/evaluations/${evaluationId}/seed-demo`, { method: "POST" }, token);
      setMessage(res.message || "Se cargaron 3 colaboradores ficticios con competencias y respuestas de ejemplo.");
      await refreshAll(token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Error al cargar datos de ejemplo");
    } finally {
      setLoading(false);
    }
  }

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
          <img src="/logo-mmarketing.png" alt="Mmarketing Logo" style={{ height: 32, width: "auto", objectFit: "contain" }} />
          <span>RRHH 360 AI</span>
        </Link>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button className="button secondary" onClick={handleSeedDemo} disabled={loading} type="button" style={{ background: "var(--accent-soft)", color: "var(--accent-dark)", border: "1px solid #b8ddd6" }}>
            ✨ Cargar Ejemplo (3 Colaboradores)
          </button>
          <button className="button secondary" onClick={() => refreshAll()} type="button">
            <RefreshCw size={16} />
            Actualizar
          </button>
        </div>
      </header>

      <section className="content">
        <div className="page-title">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <Link className="muted" href="/" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <ArrowLeft size={14} /> Volver
              </Link>
              <span className="muted" style={{ opacity: 0.4 }}>|</span>
              <span className="eyebrow" style={{ textTransform: "uppercase", fontSize: "11px", letterSpacing: "0.5px" }}>Evaluación 360</span>
            </div>
            <h1>{evaluation?.title || "Evaluacion"}</h1>
            <p className="muted">{evaluation?.description || "Sin descripcion"}</p>
          </div>
          <div className="toolbar">
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span className="eyebrow" style={{ margin: 0, textTransform: "none", fontSize: "11px", fontWeight: "bold" }}>Tipo:</span>
              <select
                className="select"
                style={{ minHeight: 28, height: 28, width: "auto", padding: "0 8px", fontSize: "0.75rem", fontWeight: "bold", border: "1px solid var(--line-strong)", borderRadius: "6px", cursor: "pointer", background: "var(--surface-soft)", color: "var(--text)" }}
                value={evaluation?.assessment_type || "individual_contributor"}
                onChange={(e) => handleAssessmentTypeChange(e.target.value)}
                disabled={loading}
              >
                <option value="individual_contributor">Contribuidor Individual</option>
                <option value="leader">Líder / Manager</option>
              </select>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span className="eyebrow" style={{ margin: 0, textTransform: "none", fontSize: "11px", fontWeight: "bold" }}>Estado:</span>
              <select
                className="select"
                style={{ minHeight: 28, height: 28, width: "auto", padding: "0 8px", fontSize: "0.75rem", fontWeight: "bold", border: "1px solid var(--line-strong)", borderRadius: "6px", cursor: "pointer", background: "var(--surface-soft)", color: "var(--text)" }}
                value={evaluation?.status || "draft"}
                onChange={(e) => handleStatusChange(e.target.value)}
                disabled={loading}
              >
                <option value="draft">Borrador</option>
                <option value="active">Activa</option>
                <option value="completed">Finalizada</option>
              </select>
            </div>
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
            className={`page-tab ${activeTab === "dispatch" ? "active" : ""}`}
            onClick={() => setActiveTab("dispatch")}
            type="button"
          >
            Centro de Envíos
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
                  <label>Competencia</label>
                  <select 
                    className="select" 
                    name="competency_bank_select" 
                    required 
                    onChange={(e) => {
                      const val = e.target.value;
                      setIsCustomCompetency(val === "custom");
                      if (val !== "custom") {
                        const selectedBank = competencyBankOptions.find(b => b.id === val);
                        if (selectedBank) {
                          setPrefilledDesc(selectedBank.description || "");
                        } else {
                          setPrefilledDesc("");
                        }
                      } else {
                        setPrefilledDesc("");
                      }
                    }}
                  >
                    <option value="">-- Selecciona una competencia --</option>
                    {competencyBankOptions.map((bankComp) => (
                      <option key={bankComp.id} value={bankComp.id}>{bankComp.name}</option>
                    ))}
                    <option value="custom">✏️ Crear competencia personalizada...</option>
                  </select>
                </div>
                {isCustomCompetency && (
                  <div className="field">
                    <label>Nombre de Competencia Personalizada</label>
                    <input className="input" name="custom_name" required placeholder="Ej: Liderazgo" />
                  </div>
                )}
                <div className="field">
                  <label>Descripcion</label>
                  <textarea 
                    className="textarea" 
                    name="description" 
                    value={prefilledDesc} 
                    onChange={(e) => setPrefilledDesc(e.target.value)} 
                    placeholder="Describe los comportamientos clave de esta competencia..."
                  />
                </div>
                <div className="field">
                  <label>Peso (%)</label>
                  <input className="input" defaultValue="100" min="10" max="100" name="weight" step="10" type="number" />
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
                        <input className="input" defaultValue={Math.round(Number(competency.weight) * 100)} min="10" max="100" name="weight" step="10" type="number" />
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
                          <span className="status-pill">Peso {Math.round(Number(competency.weight) * 100)}%</span>
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
                  <select 
                    className="select" 
                    defaultValue={firstCompetency} 
                    name="competency_id" 
                    required
                    onChange={(e) => {
                      setSelectedCompForSuggestion(e.target.value);
                      setSelectedPresetQuestions([]);
                    }}
                  >
                    {competencies.map((competency) => (
                      <option key={competency.id} value={competency.id}>
                        {competency.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Pregunta (Autoevaluado / Evaluado)</label>
                  <textarea className="textarea" name="text_self" placeholder="Ej: ¿Cómo reacciona ante una situación de crisis?" required />
                </div>
                <div className="field">
                  <label>Etiqueta Autoevaluado</label>
                  <input className="input" name="tag_self" placeholder="Ej: P1 Autoevaluado" />
                </div>
                <div className="field">
                  <label>Pregunta (Evaluadores / Espejo)</label>
                  <textarea className="textarea" name="text_evaluator" placeholder="Ej: ¿Cómo reacciona el colaborador ante una situación de crisis?" required />
                </div>
                <div className="field">
                  <label>Etiqueta Evaluador</label>
                  <input className="input" name="tag_evaluator" placeholder="Ej: P1B Evaluador" />
                </div>
                <div className="field">
                  <label>Tipo de Pregunta</label>
                  <select className="select" defaultValue="numeric_1_10" name="question_type" required>
                    <option value="numeric_1_10">Escala Numérica (1-4)</option>
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
                <div className="field" style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 12 }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span>Uso Estadístico (Evaluativa vs Informativa)</span>
                    <span title="Preguntas evaluativas impactan en las puntuaciones y promedios del reporte. Preguntas informativas solo recolectan comentarios cualitativos sin afectar los puntajes." style={{ cursor: "help", display: "inline-flex", alignItems: "center", justifyContent: "center", width: 14, height: 14, borderRadius: "50%", background: "#edf1f6", color: "#263244", fontSize: 10, fontWeight: "bold" }}>
                      ?
                    </span>
                  </label>
                  <select className="select" defaultValue="true" name="is_evaluative" style={{ width: "100%", minHeight: 34, padding: "4px 8px" }}>
                    <option value="true">Sí (Evaluativa - suma al promedio de competencia)</option>
                    <option value="false">No (Informativa / Cualitativa únicamente)</option>
                  </select>
                  <span className="muted" style={{ fontSize: "0.75rem", marginTop: 2 }}>
                    💡 <strong>Evaluativa</strong>: Aporta una calificación numérica al promedio ponderado. <strong>Informativa</strong>: recopila retroalimentación cualitativa sin alterar las notas.
                  </span>
                </div>
                <div className="field" style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}>
                  <input type="checkbox" id="save_to_bank" name="save_to_bank" value="true" style={{ cursor: "pointer" }} />
                  <label htmlFor="save_to_bank" style={{ cursor: "pointer", fontSize: "0.85rem", fontWeight: 500 }}>
                    ¿Guardar esta pregunta en el banco de preguntas sugeridas?
                  </label>
                </div>
                <input name="position" type="hidden" value={questions.length + 1} />
                <button className="button" disabled={loading || !competencies.length} type="submit" style={{ marginTop: 12 }}>
                  <Plus size={16} />
                  Agregar Pregunta
                </button>
              </form>

              {/* Banco de Preguntas Sugeridas */}
              {(() => {
                const activeComp = competencies.find(c => c.id === (selectedCompForSuggestion || firstCompetency));
                if (!activeComp) return null;
                const compName = activeComp.name;

                if (suggestedQuestions.length === 0) return null;

                return (
                  <div style={{ marginTop: 24, padding: 14, background: "rgba(0,0,0,0.015)", borderRadius: 8, border: "1px dashed var(--line)" }}>
                    <h4 style={{ fontWeight: 700, fontSize: "0.85rem", display: "flex", alignItems: "center", gap: 6, marginBottom: 8, color: "var(--accent-dark)" }}>
                      📚 Banco de Preguntas Sugeridas
                    </h4>
                    <p className="muted" style={{ fontSize: "0.75rem", marginBottom: 10 }}>
                      Hemos encontrado preguntas sugeridas para "{compName}". Marca las que desees para agregarlas:
                    </p>
                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                      {suggestedQuestions.map((q) => {
                        const isChecked = selectedPresetQuestions.includes(q.id);
                        return (
                          <label key={q.id} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: "0.8rem", cursor: "pointer" }}>
                            <input
                              type="checkbox"
                              checked={isChecked}
                              style={{ marginTop: 2 }}
                              onChange={() => {
                                setSelectedPresetQuestions(prev => 
                                  isChecked ? prev.filter(id => id !== q.id) : [...prev, q.id]
                                );
                              }}
                            />
                            <div>
                              <span>{q.text}</span>
                              <span className="muted" style={{ fontSize: "0.7rem", marginLeft: 6 }}>
                                ({q.question_type === "numeric_1_10" ? "Escala 1-4" : q.question_type.toUpperCase()})
                              </span>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                    {selectedPresetQuestions.length > 0 && (
                      <button
                        type="button"
                        className="button"
                        style={{ marginTop: 12, padding: "5px 10px", fontSize: "0.8rem", minHeight: 32 }}
                        onClick={async () => {
                          const selectedPresets = suggestedQuestions.filter(q => selectedPresetQuestions.includes(q.id));
                          await addPresetQuestions(selectedPresets, activeComp.id);
                          setSelectedPresetQuestions([]);
                        }}
                        disabled={loading}
                      >
                        Cargar {selectedPresetQuestions.length} seleccionadas
                      </button>
                    )}
                  </div>
                );
              })()}
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
                          <label>Pregunta (Autoevaluado)</label>
                          <textarea className="textarea" defaultValue={question.text_self || question.text} name="text_self" required />
                        </div>
                        <div className="field">
                          <label>Etiqueta Autoevaluado</label>
                          <input className="input" defaultValue={question.tag_self || ""} name="tag_self" placeholder="Ej: P1 Autoevaluado" />
                        </div>
                        <div className="field">
                          <label>Pregunta (Evaluador)</label>
                          <textarea className="textarea" defaultValue={question.text_evaluator || question.text} name="text_evaluator" required />
                        </div>
                        <div className="field">
                          <label>Etiqueta Evaluador</label>
                          <input className="input" defaultValue={question.tag_evaluator || ""} name="tag_evaluator" placeholder="Ej: P1B Evaluador" />
                        </div>
                        <div className="field">
                          <label>Tipo</label>
                          <select className="select" defaultValue={question.question_type || "numeric_1_10"} name="question_type" required>
                            <option value="numeric_1_10">Escala Numérica (1-4)</option>
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
                          <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <span>Uso Estadístico</span>
                            <span title="Preguntas evaluativas impactan en las puntuaciones y promedios del reporte. Preguntas informativas solo recolectan comentarios cualitativos sin afectar los puntajes." style={{ cursor: "help", display: "inline-flex", alignItems: "center", justifyContent: "center", width: 14, height: 14, borderRadius: "50%", background: "#edf1f6", color: "#263244", fontSize: 10, fontWeight: "bold" }}>
                              ?
                            </span>
                          </label>
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
                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          <div>
                            {question.tag_self && (
                              <span className="status-pill" style={{ fontSize: "0.7rem", padding: "1px 5px", marginRight: 6, background: "rgba(0,0,0,0.05)", color: "var(--accent-dark)", border: "1px solid var(--line)" }}>
                                {question.tag_self}
                              </span>
                            )}
                            <strong>Autoevaluado:</strong> {question.text_self || question.text}
                          </div>
                          <div style={{ marginTop: 4 }}>
                            {question.tag_evaluator && (
                              <span className="status-pill" style={{ fontSize: "0.7rem", padding: "1px 5px", marginRight: 6, background: "rgba(0,0,0,0.05)", color: "var(--accent-dark)", border: "1px solid var(--line)" }}>
                                {question.tag_evaluator}
                              </span>
                            )}
                            <strong>Evaluador:</strong> {question.text_evaluator || question.text}
                          </div>
                        </div>
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
              <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
                <h2>Participantes</h2>
                <div className="toolbar" style={{ gap: 8 }}>
                  <button
                    type="button"
                    className="button secondary"
                    onClick={handleDownloadParticipantsTemplate}
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
                      onChange={handleParticipantsExcelUpload}
                      disabled={loading}
                    />
                  </label>
                </div>
              </div>
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

            <section className="panel panel-relations">
              <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
                <h2>Asignaciones</h2>
                <button
                  type="button"
                  className="button secondary"
                  style={{ fontSize: "0.8rem", padding: "6px 12px", margin: 0, display: "flex", alignItems: "center", gap: 4 }}
                  onClick={handleExportLinks}
                  disabled={loading || !assignments.length}
                >
                  <LinkIcon size={14} />
                  Exportar Links (Excel)
                </button>
              </div>
              <form className="form" onSubmit={addAssignment} style={{ marginTop: 14 }}>
                <div className="field">
                  <label>Evaluado</label>
                  <select 
                    className="select" 
                    name="evaluatee_id" 
                    required
                    value={selectedEvaluateeId}
                    onChange={(e) => setSelectedEvaluateeId(e.target.value)}
                  >
                    {participants.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.full_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Evaluador</label>
                  <select className="select" name="evaluator_id" required>
                    <option value="">-- Selecciona --</option>
                    {participants
                      .filter((p) => p.id !== selectedEvaluateeId)
                      .map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.full_name}
                        </option>
                      ))}
                  </select>
                </div>
                <div className="field">
                  <label>Relacion</label>
                  <select className="select" name="relationship">
                    <option value="peer">Par</option>
                    <option value="direct_report">Reporte Directo</option>
                    <option value="line_manager">Líder directo</option>
                    <option value="indirect_manager">Líder indirecto</option>
                    <option value="external_client">Cliente Externo</option>
                    <option value="internal_client">Cliente Interno</option>
                  </select>
                </div>
                <div className="field">
                  <label>Peso (%)</label>
                  <input className="input" defaultValue="100" min="10" max="100" name="weight" step="10" type="number" />
                </div>
                <button className="button" disabled={loading || participants.length < 2} type="submit">
                  <ClipboardList size={16} />
                  Asignar
                </button>
              </form>
              <div className="list">
                {sortedAssignments.map((assignment) => {
                  const relFriendlyNames: Record<string, string> = {
                    self: "Autoevaluación",
                    peer: "Par",
                    direct_report: "Reporte Directo",
                    line_manager: "Líder directo",
                    indirect_manager: "Líder indirecto",
                    external_client: "Cliente Externo",
                    internal_client: "Cliente Interno",
                  };
                  const relLabel = relFriendlyNames[assignment.relationship] || assignment.relationship;

                  return (
                    <div 
                      className="item" 
                      key={assignment.id} 
                      style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    >
                      <div>
                        <strong>{assignment.evaluatorName}</strong>
                        <span className="muted" style={{ margin: "0 6px" }}>evalúa a</span>
                        <strong>{assignment.evaluateeName}</strong>
                        <span className="muted" style={{ marginLeft: 6, fontSize: "0.8rem" }}>({relLabel})</span>
                        <span className="status-pill" style={{ marginLeft: 8, fontSize: "0.75rem", padding: "1px 5px" }}>
                          Peso: {Math.round(Number(assignment.weight) * 100)}%
                        </span>
                      </div>
                      <div className="toolbar" style={{ gap: 6 }}>
                        <button
                          className="button danger"
                          onClick={() => deleteResource(`/evaluations/${evaluationId}/assignments/${assignment.id}`, "asignación")}
                          type="button"
                          style={{ minHeight: 30, height: 30, padding: "2px 8px", fontSize: "0.75rem" }}
                        >
                          <Trash2 size={12} />
                          Borrar
                        </button>
                      </div>
                    </div>
                  );
                })}
                {!sortedAssignments.length && <div className="empty-state">No hay relaciones configuradas aún.</div>}
              </div>
            </section>
          </div>
        )}

        {activeTab === "dispatch" && (
          <div className="dispatch-container">
            <div className="panel" style={{ background: "var(--accent-soft)", borderColor: "var(--line-strong)", color: "var(--text)", borderRadius: 12, padding: "16px 20px" }}>
              <h4 style={{ margin: 0, fontWeight: 800, fontSize: "0.95rem", color: "var(--accent-dark)" }}>Centro de Envíos de Encuestas</h4>
              <p style={{ margin: "6px 0 0", fontSize: "0.85rem", lineHeight: 1.4, color: "var(--text)" }}>
                Cada colaborador cuenta con dos tipos de encuestas: su <strong>Autoevaluación</strong> (personal y obligatoria, que se genera automáticamente al registrar al participante) y las encuestas de sus <strong>Evaluadores asignados</strong> (creadas en la sección de relaciones). Puedes copiar los enlaces individualmente aquí o exportar el listado completo a un archivo Excel.
              </p>
            </div>
            <div className="panel" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
              <div className="dispatch-search-box">
                <Search size={16} className="dispatch-search-icon" />
                <input
                  type="text"
                  placeholder="Buscar colaborador..."
                  className="input dispatch-search-input"
                  value={dispatchSearch}
                  onChange={(e) => setDispatchSearch(e.target.value)}
                />
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                <div className="toggle-group">
                  <button
                    type="button"
                    className={`toggle-btn ${viewMode === "table" ? "active" : ""}`}
                    onClick={() => setViewMode("table")}
                    title="Vista Planilla"
                  >
                    <Table size={14} />
                    Planilla
                  </button>
                  <button
                    type="button"
                    className={`toggle-btn ${viewMode === "cards" ? "active" : ""}`}
                    onClick={() => setViewMode("cards")}
                    title="Vista Mosaicos"
                  >
                    <LayoutGrid size={14} />
                    Mosaicos
                  </button>
                </div>
                <button
                  type="button"
                  className="button"
                  style={{ display: "flex", alignItems: "center", gap: 6 }}
                  onClick={handleExportLinks}
                  disabled={loading || !assignments.length}
                >
                  <LinkIcon size={14} />
                  Exportar Todos los Links (Excel)
                </button>
              </div>
            </div>

            {participants.length === 0 ? (
              <div className="empty-state">No hay participantes registrados en esta evaluación. Agrégalos en la pestaña de Participantes.</div>
            ) : (
              (() => {
                const filtered = participants.filter(
                  (p) =>
                    p.full_name.toLowerCase().includes(dispatchSearch.toLowerCase()) ||
                    p.email.toLowerCase().includes(dispatchSearch.toLowerCase())
                );

                if (filtered.length === 0) {
                  return <div className="empty-state">No se encontraron colaboradores que coincidan con la búsqueda.</div>;
                }

                const relFriendlyNames: Record<string, string> = {
                  self: "Autoevaluación",
                  peer: "Par",
                  direct_report: "Reporte Directo",
                  line_manager: "Líder directo",
                  indirect_manager: "Líder indirecto",
                  external_client: "Cliente Externo",
                  internal_client: "Cliente Interno",
                };

                if (viewMode === "table") {
                  return (
                    <div className="dispatch-table-container">
                      <table className="dispatch-table">
                        <thead>
                          <tr>
                            <th style={{ width: "35%" }}>Colaborador (Evaluado)</th>
                            <th style={{ width: "25%" }}>Autoevaluación</th>
                            <th style={{ width: "25%" }}>Progreso Espejo</th>
                            <th style={{ width: "15%", textAlign: "center" }}>Acciones</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filtered.map((participant) => {
                            const participantAssignments = assignments.filter((a) => a.evaluatee_id === participant.id);
                            
                            // Autoevaluación assignment
                            const selfAssignment = participantAssignments.find((a) => a.relationship === "self");
                            const isSelfCompleted = selfAssignment?.is_completed ?? false;
                            const selfLink = selfAssignment?.survey_token ? `${window.location.origin}/survey/${selfAssignment.survey_token}` : "";

                            // Evaluadores (relaciones espejo)
                            const mirrorAssignments = participantAssignments.filter((a) => a.relationship !== "self");
                            const totalMirror = mirrorAssignments.length;
                            const completedMirror = mirrorAssignments.filter((a) => a.is_completed).length;
                            const progressPercent = totalMirror > 0 ? Math.round((completedMirror / totalMirror) * 100) : 0;

                            const isExpanded = !!expandedEvaluatees[participant.id];

                            const toggleExpand = (e: React.MouseEvent) => {
                              // Evitar que el clic en un botón propague el clic a la fila
                              if ((e.target as HTMLElement).closest('button') || (e.target as HTMLElement).closest('a')) {
                                return;
                              }
                              setExpandedEvaluatees((prev) => ({
                                ...prev,
                                [participant.id]: !prev[participant.id],
                              }));
                            };

                            return (
                              <Fragment key={participant.id}>
                                <tr 
                                  className={`evaluatee-row ${isExpanded ? "expanded" : ""}`}
                                  onClick={toggleExpand}
                                >
                                  <td>
                                    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                                      <span style={{ fontWeight: 800, fontSize: "14px" }}>{participant.full_name}</span>
                                      <span className="muted" style={{ fontSize: "11px" }}>{participant.role || "Sin rol definido"} • {participant.email}</span>
                                    </div>
                                  </td>
                                  <td>
                                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                      <span className={`dispatch-status ${isSelfCompleted ? "completed" : "pending"}`} style={{ fontSize: "9px" }}>
                                        {isSelfCompleted ? "Completada" : "Pendiente"}
                                      </span>
                                      {selfAssignment && selfLink && (
                                        <div style={{ display: "flex", gap: 4 }}>
                                          <button
                                            onClick={() => handleCopy(selfLink, selfAssignment.id)}
                                            className={`copy-btn-interactive ${copiedId === selfAssignment.id ? "copied" : ""}`}
                                            style={{ minHeight: "24px", height: "24px", padding: "2px 6px", fontSize: "10px" }}
                                            title="Copiar link autoevaluación"
                                          >
                                            {copiedId === selfAssignment.id ? <Check size={10} /> : <Copy size={10} />}
                                            {copiedId === selfAssignment.id ? "Copiado" : "Copiar"}
                                          </button>
                                          <a href={selfLink} target="_blank" rel="noreferrer" className="copy-btn-interactive" style={{ minHeight: "24px", height: "24px", width: "24px", padding: 0 }} title="Ver encuesta en vivo">
                                            <ExternalLink size={10} />
                                          </a>
                                        </div>
                                      )}
                                    </div>
                                  </td>
                                  <td>
                                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", fontWeight: "bold" }}>
                                        <span className="muted">{completedMirror} de {totalMirror} completadas</span>
                                        <span style={{ color: "var(--accent-dark)" }}>{progressPercent}%</span>
                                      </div>
                                      <div className="progress-track">
                                        <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
                                      </div>
                                    </div>
                                  </td>
                                  <td style={{ textAlign: "center" }}>
                                    <button
                                      type="button"
                                      className="button secondary"
                                      onClick={() => setExpandedEvaluatees((prev) => ({ ...prev, [participant.id]: !prev[participant.id] }))}
                                      style={{ minHeight: "28px", height: "28px", padding: "4px 10px", fontSize: "11px", display: "inline-flex", alignItems: "center", gap: 4 }}
                                    >
                                      {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                                      {isExpanded ? "Ocultar" : `Evaluadores (${totalMirror})`}
                                    </button>
                                  </td>
                                </tr>

                                {isExpanded && (
                                  <tr className="expanded-row">
                                    <td colSpan={4}>
                                      <div className="expanded-row-content">
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                          <h5 style={{ margin: 0, fontSize: "11px", textTransform: "uppercase", color: "var(--muted)", letterSpacing: "0.5px" }}>
                                            Evaluadores asignados para {participant.full_name}
                                          </h5>
                                        </div>
                                        {totalMirror === 0 ? (
                                          <div style={{ textAlign: "center", padding: "12px", color: "var(--muted)", fontStyle: "italic", fontSize: "12px" }}>
                                            No se han asignado evaluadores para este colaborador.
                                          </div>
                                        ) : (
                                          <div className="expanded-grid">
                                            {mirrorAssignments.map((assignment) => {
                                              const evaluator = participants.find((p) => p.id === assignment.evaluator_id);
                                              const evaluatorName = evaluator ? evaluator.full_name : "Desconocido";
                                              const link = assignment.survey_token ? `${window.location.origin}/survey/${assignment.survey_token}` : "";
                                              const isComp = assignment.is_completed ?? false;

                                              return (
                                                <div className="expanded-card" key={assignment.id}>
                                                  <div style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0, flexGrow: 1 }}>
                                                    <span style={{ fontWeight: 700, fontSize: "12px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={evaluatorName}>
                                                      {evaluatorName}
                                                    </span>
                                                    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                                                      <span className="dispatch-relationship">
                                                        {relFriendlyNames[assignment.relationship] || assignment.relationship}
                                                      </span>
                                                      <span className={`dispatch-status ${isComp ? "completed" : "pending"}`} style={{ fontSize: "8px", padding: "1px 5px" }}>
                                                        {isComp ? "Completada" : "Pendiente"}
                                                      </span>
                                                    </div>
                                                  </div>
                                                  {link && (
                                                    <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
                                                      <button
                                                        onClick={() => handleCopy(link, assignment.id)}
                                                        className={`copy-btn-interactive ${copiedId === assignment.id ? "copied" : ""}`}
                                                        style={{ minHeight: "24px", height: "24px", padding: "2px 6px", fontSize: "10px" }}
                                                      >
                                                        {copiedId === assignment.id ? <Check size={10} /> : <Copy size={10} />}
                                                        {copiedId === assignment.id ? "Copiado" : "Copiar"}
                                                      </button>
                                                      <a href={link} target="_blank" rel="noreferrer" className="copy-btn-interactive" style={{ minHeight: "24px", height: "24px", width: "24px", padding: 0 }} title="Ver encuesta en vivo">
                                                        <ExternalLink size={10} />
                                                      </a>
                                                    </div>
                                                  )}
                                                </div>
                                              );
                                            })}
                                          </div>
                                        )}
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </Fragment>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  );
                }

                return (
                  <div className="dispatch-grid">
                    {filtered.map((participant) => {
                      const participantAssignments = assignments.filter((a) => a.evaluatee_id === participant.id);
                      
                      // Autoevaluación assignment
                      const selfAssignment = participantAssignments.find((a) => a.relationship === "self");
                      const isSelfCompleted = selfAssignment?.is_completed ?? false;
                      const selfLink = selfAssignment?.survey_token ? `${window.location.origin}/survey/${selfAssignment.survey_token}` : "";

                      // Evaluadores (relaciones espejo)
                      const mirrorAssignments = participantAssignments.filter((a) => a.relationship !== "self");
                      const totalMirror = mirrorAssignments.length;
                      const completedMirror = mirrorAssignments.filter((a) => a.is_completed).length;

                      const progressPercent = totalMirror > 0 ? Math.round((completedMirror / totalMirror) * 100) : 0;
                      
                      const initials = participant.full_name
                        .split(" ")
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join("")
                        .toUpperCase();

                      return (
                        <div className="dispatch-card" key={participant.id}>
                          <div className="dispatch-card-header">
                            <div className="dispatch-avatar">{initials}</div>
                            <div className="dispatch-user-info">
                              <span className="dispatch-name" title={participant.full_name}>{participant.full_name}</span>
                              <span className="dispatch-role" title={participant.role || "Sin rol"}>{participant.role || "Sin rol definido"}</span>
                              <span className="muted" style={{ fontSize: "11px" }}>{participant.email}</span>
                            </div>
                          </div>

                          {/* Autoevaluación Section */}
                          <div className="dispatch-section">
                            <div className="dispatch-section-header">
                              <span className="dispatch-section-title">Autoevaluación</span>
                              <span className={`dispatch-status ${isSelfCompleted ? "completed" : "pending"}`}>
                                {isSelfCompleted ? "Completada" : "Pendiente"}
                              </span>
                            </div>
                            {selfAssignment && selfLink ? (
                              <div className="dispatch-row" style={{ padding: "4px 0" }}>
                                <span className="muted" style={{ fontSize: "12px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "160px" }} title={selfLink}>
                                  {selfLink}
                                </span>
                                <div style={{ display: "flex", gap: 6 }}>
                                  <button
                                    onClick={() => handleCopy(selfLink, selfAssignment.id)}
                                    className={`copy-btn-interactive ${copiedId === selfAssignment.id ? "copied" : ""}`}
                                    title="Copiar link de autoevaluación"
                                  >
                                    {copiedId === selfAssignment.id ? <Check size={12} /> : <Copy size={12} />}
                                    {copiedId === selfAssignment.id ? "Copiado" : "Copiar"}
                                  </button>
                                  <a href={selfLink} target="_blank" rel="noreferrer" className="copy-btn-interactive" title="Ver encuesta en vivo">
                                    <ExternalLink size={12} />
                                  </a>
                                </div>
                              </div>
                            ) : (
                              <span className="muted" style={{ fontSize: "12px" }}>No configurada</span>
                            )}
                          </div>

                          {/* Mirror/Evaluator Progress Section */}
                          <div className="dispatch-section">
                            <div className="dispatch-section-header">
                              <span className="dispatch-section-title">Evaluadores ({totalMirror})</span>
                              <span className="muted" style={{ fontSize: "12px", fontWeight: "700" }}>{completedMirror} de {totalMirror}</span>
                            </div>
                            <div className="progress-track" style={{ margin: "4px 0" }}>
                              <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
                            </div>
                            <div className="progress-header">
                              <span className="muted" style={{ fontSize: "11px" }}>Progreso espejo</span>
                              <span style={{ color: "var(--accent-dark)", fontSize: "11px" }}>{progressPercent}%</span>
                            </div>
                          </div>

                          {/* Evaluators relationships detail list */}
                          <div className="dispatch-section" style={{ flexGrow: 1 }}>
                            <span className="dispatch-section-title" style={{ marginBottom: 4 }}>Detalle Relaciones</span>
                            {totalMirror === 0 ? (
                              <span className="muted" style={{ fontSize: "12px", fontStyle: "italic", textAlign: "center", padding: "10px 0" }}>
                                Sin evaluadores asignados
                              </span>
                            ) : (
                              <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: "200px", overflowY: "auto", paddingRight: "4px" }}>
                                {mirrorAssignments.map((assignment) => {
                                  const evaluator = participants.find((p) => p.id === assignment.evaluator_id);
                                  const evaluatorName = evaluator ? evaluator.full_name : "Desconocido";
                                  const link = assignment.survey_token ? `${window.location.origin}/survey/${assignment.survey_token}` : "";
                                  const isComp = assignment.is_completed ?? false;

                                  return (
                                    <div className="dispatch-row" key={assignment.id} style={{ borderBottom: "1px solid rgba(216, 222, 232, 0.3)", paddingBottom: "6px" }}>
                                      <div style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0, flexGrow: 1 }}>
                                        <span style={{ fontWeight: 700, fontSize: "12px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={evaluatorName}>
                                          {evaluatorName}
                                        </span>
                                        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                                          <span className="dispatch-relationship">
                                            {relFriendlyNames[assignment.relationship] || assignment.relationship}
                                          </span>
                                          <span className={`dispatch-status ${isComp ? "completed" : "pending"}`} style={{ fontSize: "8px", padding: "1px 5px" }}>
                                            {isComp ? "Listo" : "Pendiente"}
                                          </span>
                                        </div>
                                      </div>
                                      {link ? (
                                        <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
                                          <button
                                            onClick={() => handleCopy(link, assignment.id)}
                                            className={`copy-btn-interactive ${copiedId === assignment.id ? "copied" : ""}`}
                                            style={{ minHeight: "24px", height: "24px", padding: "2px 6px", fontSize: "10px" }}
                                            title="Copiar enlace"
                                          >
                                            {copiedId === assignment.id ? <Check size={10} /> : <Copy size={10} />}
                                            {copiedId === assignment.id ? "Copiado" : "Copiar"}
                                          </button>
                                          <a href={link} target="_blank" rel="noreferrer" className="copy-btn-interactive" style={{ minHeight: "24px", height: "24px", width: "24px", padding: 0 }} title="Ver encuesta en vivo">
                                            <ExternalLink size={10} />
                                          </a>
                                        </div>
                                      ) : null}
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })()
            )}
          </div>
        )}

        {activeTab === "results" && (
          <div className="results-container">
            {/* Sub-tab navigation selector & Export Actions */}
            <div className="panel" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18, padding: "12px 16px", flexWrap: "wrap", gap: 12 }}>
              <div className="toggle-group" style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className={`toggle-btn ${resultsSubTab === "general" ? "active" : ""}`}
                  onClick={() => setResultsSubTab("general")}
                  style={{ padding: "6px 14px", fontSize: "0.85rem", fontWeight: "bold" }}
                >
                  📊 Vista General
                </button>
                <button
                  type="button"
                  className={`toggle-btn ${resultsSubTab === "participant" ? "active" : ""}`}
                  onClick={() => setResultsSubTab("participant")}
                  style={{ padding: "6px 14px", fontSize: "0.85rem", fontWeight: "bold" }}
                >
                  👤 Por Colaborador
                </button>
                <button
                  type="button"
                  className={`toggle-btn ${resultsSubTab === "executive" ? "active" : ""}`}
                  onClick={() => {
                    setResultsSubTab("executive");
                    if (!executiveResults) void loadExecutiveReport();
                  }}
                  style={{
                    padding: "6px 14px",
                    fontSize: "0.85rem",
                    fontWeight: "bold",
                    background: resultsSubTab === "executive" ? "#00857c" : undefined,
                    color: resultsSubTab === "executive" ? "#ffffff" : undefined,
                  }}
                >
                  📑 Reporte Ejecutivo 360° (MSD 29P)
                </button>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                {resultsSubTab === "participant" && (
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span className="eyebrow" style={{ margin: 0, textTransform: "none", fontSize: "12px", fontWeight: "bold" }}>Colaborador:</span>
                    <select
                      className="select"
                      style={{ minWidth: 200, height: 36, padding: "0 10px", fontSize: "0.85rem", fontWeight: "bold", border: "1px solid var(--line-strong)", borderRadius: "8px", cursor: "pointer" }}
                      value={selectedParticipantForReport}
                      onChange={(e) => setSelectedParticipantForReport(e.target.value)}
                    >
                      <option value="">-- Selecciona un colaborador --</option>
                      {participants.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.full_name} ({p.role || "Sin rol"})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <button
                  type="button"
                  className="button secondary"
                  onClick={() => setShowReportConfigModal(true)}
                  style={{
                    height: 36,
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "0 12px",
                    border: "1px solid #00857c",
                    color: "#00857c",
                    background: "rgba(0,133,124,0.06)",
                    borderRadius: "8px",
                    cursor: "pointer",
                  }}
                  title="Configurar logotipos corporativos, títulos, narrativa y umbrales semafóricos"
                >
                  <Settings size={15} />
                  Configurar Informe
                </button>

                <button
                  type="button"
                  className="button primary"
                  onClick={handleDownloadExecutivePdf}
                  disabled={downloadingExecutivePdf}
                  style={{
                    height: 36,
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "0 12px",
                    background: "#00857c",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "8px",
                    boxShadow: "0 2px 4px rgba(0,133,124,0.2)",
                    cursor: "pointer",
                  }}
                  title="Descargar Reporte Ejecutivo Oficial de 29 páginas idéntico al formato original"
                >
                  <FileText size={15} />
                  {downloadingExecutivePdf ? "Generando 29 Págs..." : "Reporte Ejecutivo (PDF 29P)"}
                </button>

                <button
                  type="button"
                  className="button secondary"
                  onClick={handleDownloadGeneralPdf}
                  disabled={downloadingGeneralPdf}
                  style={{ height: 36, fontSize: "0.82rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 6, padding: "0 12px", border: "1px solid var(--accent)", color: "var(--accent-dark)", background: "var(--accent-soft)" }}
                  title="Descargar Informe General en PDF"
                >
                  <FileText size={15} />
                  {downloadingGeneralPdf ? "Generando PDF..." : "PDF General"}
                </button>

                <button
                  type="button"
                  className="button secondary"
                  onClick={handleDownloadZip}
                  disabled={downloadingZip}
                  style={{ height: 36, fontSize: "0.82rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 6, padding: "0 12px", border: "1px solid var(--line-strong)", background: "#ffffff", color: "var(--foreground)" }}
                  title="Descargar ZIP con los PDFs de todos los colaboradores"
                >
                  <FileArchive size={15} />
                  {downloadingZip ? "Generando ZIP..." : "Todos (ZIP)"}
                </button>
              </div>
            </div>


            {resultsSubTab === "general" && (
              <>
                {results?.outliers && results.outliers.length > 0 && (evaluation?.report_config?.show_picos_alert !== false) && (
                  <div className="panel" style={{ background: "#fff8e6", border: "1px solid #ffe58f", borderRadius: 12, padding: "16px 20px", marginBottom: 18 }}>
                    <h4 style={{ margin: 0, fontWeight: 800, fontSize: "0.95rem", color: "#b78103", display: "flex", alignItems: "center", gap: 8 }}>
                      ⚠️ Alertas de Picos en Evaluaciones ({results.outliers.length})
                    </h4>
                    <p style={{ margin: "4px 0 12px", fontSize: "0.85rem", color: "#594206" }}>
                      Se han detectado discrepancias significativas en las calificaciones otorgadas por algunos evaluadores respecto al consenso del grupo:
                    </p>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {results.outliers.map((alert, idx) => (
                        <div key={idx} style={{ background: "#ffffff", padding: "10px 14px", borderRadius: 8, border: "1px solid #ffd591", fontSize: "0.85rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div>
                            <strong>{alert.evaluator_name}</strong> → <strong>{alert.evaluatee_name}</strong>
                            <p style={{ margin: "2px 0 0", color: "#666", fontSize: "0.8rem" }}>{alert.message}</p>
                          </div>
                          <span className="status-pill" style={{ background: alert.alert_type === "high_outlier" ? "var(--accent-soft)" : "#fff1f0", color: alert.alert_type === "high_outlier" ? "var(--accent-dark)" : "#cf1322", border: alert.alert_type === "high_outlier" ? "1px solid #b8ddd6" : "1px solid #ffa39e", fontWeight: "bold", fontSize: "0.75rem", whiteSpace: "nowrap" }}>
                            {alert.alert_type === "high_outlier" ? "Pico Positivo (+)" : "Pico Negativo (-)"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

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

            {resultsSubTab === "participant" && (
              <div>
                {loadingParticipantReport ? (
                  <div className="empty-state">Cargando reporte individual del colaborador...</div>
                ) : !participantReport ? (
                  <div className="empty-state">Selecciona un colaborador para consultar su informe estadístico 360°.</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                    {/* Header del Colaborador */}
                    <div className="panel" style={{ background: "var(--surface-soft)", borderRadius: 12, padding: "18px 22px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
                        <div>
                          <span className="eyebrow" style={{ textTransform: "uppercase", fontSize: "11px", letterSpacing: "0.5px" }}>Reporte Individual 360°</span>
                          <h2 style={{ margin: "2px 0 4px", fontSize: "1.4rem" }}>{participantReport.participant_name}</h2>
                          <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
                            {participantReport.participant_role || "Sin rol definido"} • {participantReport.participant_email}
                          </p>
                        </div>
                        <button
                          type="button"
                          className="button primary"
                          onClick={() => handleDownloadParticipantPdf(participantReport.participant_id)}
                          disabled={downloadingParticipantPdf}
                          style={{ height: 38, fontSize: "0.85rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 6, padding: "0 16px" }}
                        >
                          <Download size={16} />
                          {downloadingParticipantPdf ? "Generando PDF..." : "Descargar PDF Individual"}
                        </button>
                      </div>
                    </div>


                    {/* KPI Band del Colaborador */}
                    <div className="kpi-band">
                      <section className="panel metric">
                        <span className="muted">Promedio Evaluadores</span>
                        <strong style={{ color: "var(--accent-dark)" }}>{participantReport.overall_evaluators_score ?? "N/A"}</strong>
                      </section>
                      <section className="panel metric">
                        <span className="muted">Autoevaluación</span>
                        <strong>{participantReport.overall_self_score ?? "N/A"}</strong>
                      </section>
                      <section className="panel metric">
                        <span className="muted">Brecha de Percepción</span>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <strong>
                            {participantReport.overall_gap !== null && participantReport.overall_gap > 0 ? `+${participantReport.overall_gap}` : (participantReport.overall_gap ?? "N/A")}
                          </strong>
                          {participantReport.overall_gap !== null && (
                            <span 
                              className="status-pill" 
                              style={{ 
                                fontSize: "0.75rem", 
                                background: participantReport.overall_gap > 0.5 ? "#fff7e6" : participantReport.overall_gap < -0.5 ? "#e6f7ff" : "#f6ffed",
                                color: participantReport.overall_gap > 0.5 ? "#d46b08" : participantReport.overall_gap < -0.5 ? "#0958d9" : "#389e0d",
                                border: participantReport.overall_gap > 0.5 ? "1px solid #ffd591" : participantReport.overall_gap < -0.5 ? "1px solid #91caff" : "1px solid #b7eb8f"
                              }}
                            >
                              {participantReport.overall_gap > 0.5 ? "Sobreestimado" : participantReport.overall_gap < -0.5 ? "Subestimado" : "Alineado"}
                            </span>
                          )}
                        </div>
                      </section>
                    </div>

                    {/* Fortalezas y Oportunidades */}
                    <div className="grid two">
                      <section className="panel" style={{ background: "rgba(39, 174, 96, 0.03)", border: "1px solid rgba(39, 174, 96, 0.2)" }}>
                        <h3 style={{ fontSize: "1rem", color: "#27ae60", display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                          🌟 Fortalezas Destacadas
                        </h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {participantReport.top_strengths.map((str, idx) => (
                            <div key={idx} style={{ background: "#fff", padding: "8px 12px", borderRadius: 6, border: "1px solid var(--line)", fontSize: "0.85rem", fontWeight: 600 }}>
                              {str}
                            </div>
                          ))}
                          {!participantReport.top_strengths.length && <p className="muted" style={{ fontSize: "0.85rem" }}>Sin suficientes datos para evaluar fortalezas.</p>}
                        </div>
                      </section>

                      <section className="panel" style={{ background: "rgba(230, 126, 34, 0.03)", border: "1px solid rgba(230, 126, 34, 0.2)" }}>
                        <h3 style={{ fontSize: "1rem", color: "#e67e22", display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                          🎯 Áreas de Oportunidad / Desarrollo
                        </h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {participantReport.opportunities.map((opp, idx) => (
                            <div key={idx} style={{ background: "#fff", padding: "8px 12px", borderRadius: 6, border: "1px solid var(--line)", fontSize: "0.85rem", fontWeight: 600 }}>
                              {opp}
                            </div>
                          ))}
                          {!participantReport.opportunities.length && <p className="muted" style={{ fontSize: "0.85rem" }}>Sin suficientes datos para evaluar oportunidades.</p>}
                        </div>
                      </section>
                    </div>

                    {/* Tabla de Competencias por Relación */}
                    <section className="panel">
                      <h3 style={{ marginBottom: 14 }}>Desglose por Competencia y Tipo de Relación</h3>
                      <div style={{ overflowX: "auto" }}>
                        <table className="dispatch-table" style={{ fontSize: "0.85rem" }}>
                          <thead>
                            <tr>
                              <th>Competencia</th>
                              <th style={{ textAlign: "center" }}>Autoevaluación</th>
                              <th style={{ textAlign: "center" }}>Evaluadores (Promedio)</th>
                              <th style={{ textAlign: "center" }}>Brecha</th>
                              <th>Desglose por Relación</th>
                            </tr>
                          </thead>
                          <tbody>
                            {participantReport.competencies.map((comp) => (
                              <tr key={comp.competency_id}>
                                <td style={{ fontWeight: 700 }}>{comp.competency_name}</td>
                                <td style={{ textAlign: "center" }}>
                                  {comp.self_score !== null ? <strong>{comp.self_score}</strong> : <span className="muted">-</span>}
                                </td>
                                <td style={{ textAlign: "center" }}>
                                  {comp.evaluators_score !== null ? (
                                    <span className="status-pill" style={{ background: "var(--accent-soft)", color: "var(--accent-dark)", fontWeight: "bold" }}>
                                      {comp.evaluators_score}
                                    </span>
                                  ) : <span className="muted">-</span>}
                                </td>
                                <td style={{ textAlign: "center" }}>
                                  {comp.gap !== null ? (
                                    <span style={{ fontWeight: "bold", color: comp.gap > 0.5 ? "#d46b08" : comp.gap < -0.5 ? "#0958d9" : "#389e0d" }}>
                                      {comp.gap > 0 ? `+${comp.gap}` : comp.gap}
                                    </span>
                                  ) : <span className="muted">-</span>}
                                </td>
                                <td>
                                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                                    {Object.entries(comp.by_relationship).map(([rel, sc]) => (
                                      <span key={rel} className="status-pill" style={{ fontSize: "0.75rem", background: "rgba(0,0,0,0.03)", border: "1px solid var(--line)" }}>
                                        {rel}: <strong>{sc}</strong>
                                      </span>
                                    ))}
                                    {Object.keys(comp.by_relationship).length === 0 && <span className="muted" style={{ fontSize: "0.75rem" }}>Sin respuestas espejo</span>}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </section>

                    {/* Desglose de Preguntas y Comentarios */}
                    <section className="panel">
                      <h3 style={{ marginBottom: 14 }}>Preguntas y Retroalimentación Cualitativa</h3>
                      <div className="list">
                        {participantReport.questions.map((q) => (
                          <div className="item" key={q.question_id} style={{ display: "block" }}>
                            <div className="row" style={{ alignItems: "flex-start", marginBottom: 6 }}>
                              <div>
                                <span className="status-pill" style={{ marginRight: 6, fontSize: "0.7rem", padding: "1px 5px" }}>{q.competency_name}</span>
                                <h4 style={{ marginTop: 4, fontSize: "0.95rem", fontWeight: 700 }}>{q.question_text}</h4>
                              </div>
                              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                                {q.self_score !== null && (
                                  <div style={{ textAlign: "right" }}>
                                    <span className="muted" style={{ fontSize: "0.7rem", display: "block" }}>Auto</span>
                                    <strong style={{ fontSize: "0.95rem" }}>{q.self_score}</strong>
                                  </div>
                                )}
                                {q.evaluators_score !== null && (
                                  <div style={{ textAlign: "right" }}>
                                    <span className="muted" style={{ fontSize: "0.7rem", display: "block" }}>Evaluadores</span>
                                    <strong style={{ fontSize: "0.95rem", color: "var(--accent-dark)" }}>{q.evaluators_score}</strong>
                                  </div>
                                )}
                              </div>
                            </div>

                            {q.comments && q.comments.length > 0 && (
                              <div style={{ marginTop: 10, background: "rgba(0,0,0,0.015)", padding: 10, borderRadius: 6, border: "1px solid var(--line)" }}>
                                <span className="muted" style={{ fontSize: "0.75rem", fontWeight: 700, display: "block", marginBottom: 6 }}>
                                  💬 Comentarios Recibidos ({q.comments.length}):
                                </span>
                                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                  {q.comments.map((c, idx) => (
                                    <div key={idx} style={{ fontSize: "0.8rem", background: "#fff", padding: "6px 10px", borderRadius: 4, border: "1px solid var(--line)" }}>
                                      <span className="status-pill" style={{ fontSize: "0.7rem", padding: "1px 4px", marginRight: 6, background: "var(--accent-soft)", color: "var(--accent-dark)" }}>
                                        {c.relationship}
                                      </span>
                                      <em>"{c.comment}"</em>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </section>
                  </div>
                )}
              </div>
            )}

            {resultsSubTab === "executive" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                {/* Hero / Banner Ejecutivo */}
                <div
                  className="panel"
                  style={{
                    background: "linear-gradient(135deg, #00857c 0%, #005a54 100%)",
                    color: "#ffffff",
                    padding: "24px 28px",
                    borderRadius: "14px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 16,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap" }}>
                    {evaluation?.client_logo_url && (
                      <div
                        style={{
                          background: "#ffffff",
                          padding: "6px 12px",
                          borderRadius: "10px",
                          boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          maxHeight: 58,
                        }}
                      >
                        <img
                          src={evaluation.client_logo_url}
                          alt="Logo Cliente"
                          style={{ maxHeight: 42, maxWidth: 130, objectFit: "contain" }}
                        />
                      </div>
                    )}
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                        <span
                          style={{
                            background: "rgba(255,255,255,0.2)",
                            color: "#fff",
                            padding: "3px 10px",
                            borderRadius: "20px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                            textTransform: "uppercase",
                            letterSpacing: "0.5px",
                          }}
                        >
                          Reporte Oficial de Alta Dirección
                        </span>
                        {evaluation?.consultant_logo_url && (
                          <span
                            style={{
                              background: "rgba(255,255,255,0.15)",
                              color: "#fff",
                              padding: "2px 8px",
                              borderRadius: "12px",
                              fontSize: "0.72rem",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 6,
                            }}
                          >
                            <span>Consultora:</span>
                            <img
                              src={evaluation.consultant_logo_url}
                              alt="Logo Consultor"
                              style={{ maxHeight: 18, maxWidth: 65, objectFit: "contain", verticalAlign: "middle" }}
                            />
                          </span>
                        )}
                      </div>
                      <h2 style={{ fontSize: "1.45rem", fontWeight: 800, margin: "10px 0 6px 0", color: "#fff" }}>
                        {evaluation?.report_config?.cover_title_1 || "Reporte de"}{" "}
                        {evaluation?.report_config?.cover_title_2 || "Evaluación"}{" "}
                        {evaluation?.report_config?.cover_title_3 || "360°"} -{" "}
                        {evaluation?.report_config?.company_name || evaluation?.title || "MSD"}
                      </h2>
                      <p style={{ margin: 0, fontSize: "0.88rem", opacity: 0.9, maxWidth: 640 }}>
                        {evaluation?.report_config?.cover_subtitle_2 || "Fuerza de Ventas"} • {evaluation?.report_config?.header_title || "Reporte Grupal - Evaluación 360°"} (Formato corporativo 29 páginas)
                      </p>
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                    <button
                      type="button"
                      onClick={() => setShowReportConfigModal(true)}
                      style={{
                        background: "rgba(255,255,255,0.18)",
                        color: "#ffffff",
                        fontWeight: 700,
                        fontSize: "0.85rem",
                        padding: "10px 16px",
                        borderRadius: "10px",
                        border: "1px solid rgba(255,255,255,0.4)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        backdropFilter: "blur(4px)",
                      }}
                      title="Configurar logotipos corporativos, textos y umbrales semafóricos"
                    >
                      <Settings size={16} />
                      Configurar Informe
                    </button>

                    <button
                      type="button"
                      className="button"
                      onClick={handleDownloadExecutivePdf}
                      disabled={downloadingExecutivePdf}
                      style={{
                        background: "#ffffff",
                        color: "#00857c",
                        fontWeight: 800,
                        fontSize: "0.92rem",
                        padding: "10px 20px",
                        borderRadius: "10px",
                        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                        border: "none",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                      }}
                    >
                      <Download size={18} />
                      {downloadingExecutivePdf ? "Generando 29 Págs..." : "Descargar PDF (29P)"}
                    </button>
                  </div>
                </div>

                {loadingExecutive && !executiveResults && (
                  <div className="panel" style={{ textAlign: "center", padding: 40 }}>
                    <p className="muted">Calculando estadísticas ejecutivas del reporte 360°...</p>
                  </div>
                )}

                {executiveResults && (
                  <>
                    {/* Tarjetas de Métricas Generales */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
                      <div className="panel" style={{ padding: "16px 20px" }}>
                        <span className="muted" style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase" }}>Total Evaluados</span>
                        <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--foreground)", marginTop: 4 }}>
                          {executiveResults.total_evaluados}
                        </div>
                        <span className="muted" style={{ fontSize: "0.75rem" }}>Representantes analizados</span>
                      </div>

                      <div className="panel" style={{ padding: "16px 20px", borderLeft: "4px solid #00857c" }}>
                        <span className="muted" style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase" }}>Promedio Neto Global</span>
                        <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#00857c", marginTop: 4 }}>
                          {executiveResults.net_overall.average?.toFixed(2) || "0.00"}
                          <span style={{ fontSize: "0.9rem", color: "var(--muted)", fontWeight: 500 }}> / 10</span>
                        </div>
                        <span className="muted" style={{ fontSize: "0.75rem" }}>Escala 1 a 10 integrada</span>
                      </div>

                      <div className="panel" style={{ padding: "16px 20px", borderLeft: "4px solid #22c55e" }}>
                        <span className="muted" style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase" }}>Mediana Global</span>
                        <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#15803d", marginTop: 4 }}>
                          {executiveResults.net_overall.median?.toFixed(2) || "0.00"}
                        </div>
                        <span className="muted" style={{ fontSize: "0.75rem" }}>Punto de corte central</span>
                      </div>

                      <div className="panel" style={{ padding: "16px 20px", borderLeft: "4px solid #eab308" }}>
                        <span className="muted" style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase" }}>Desviación Estándar</span>
                        <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#854d0e", marginTop: 4 }}>
                          {executiveResults.net_overall.stddev?.toFixed(2) || "0.00"}
                        </div>
                        <span className="muted" style={{ fontSize: "0.75rem" }}>Dispersión general grupal</span>
                      </div>
                    </div>

                    {/* Resumen de Competencias y Ponderaciones */}
                    <div className="panel" style={{ padding: "20px 24px" }}>
                      <h3 style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: 14 }}>
                        Estructura de Competencias y Ponderaciones Estratégicas
                      </h3>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
                        {executiveResults.competencies.map((comp, idx) => (
                          <div
                            key={comp.competency_id}
                            style={{
                              background: "#f8fafc",
                              border: "1px solid #e2e8f0",
                              borderRadius: "10px",
                              padding: "14px 16px",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
                                {idx + 1}. {comp.competency_name}
                              </span>
                              <span
                                style={{
                                  background: "#00857c",
                                  color: "#fff",
                                  fontSize: "0.72rem",
                                  fontWeight: 800,
                                  padding: "2px 7px",
                                  borderRadius: "6px",
                                }}
                              >
                                {comp.weight_pct.toFixed(0)}%
                              </span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", marginBottom: 4 }}>
                              <span className="muted">Promedio Neto:</span>
                              <strong>{comp.net_average.toFixed(2)}</strong>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", marginBottom: 4 }}>
                              <span className="muted">Mediana:</span>
                              <span>{comp.net_median.toFixed(2)}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                              <span className="muted">Reactivos:</span>
                              <span>{comp.items.length} ítems</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Principales Hallazgos (Insights) */}
                    {executiveResults.insights && (evaluation?.report_config?.show_insights_section !== false) && (
                      <div className="panel" style={{ padding: "20px 24px" }}>
                        <h3 style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: 12 }}>
                          Principales Hallazgos y Análisis Estratégico
                        </h3>
                        <ul style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 8, fontSize: "0.88rem", color: "#334155" }}>
                          {executiveResults.insights.summary_bullets.map((b, idx) => (
                            <li key={idx} style={{ lineHeight: 1.5 }}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Matriz de Ranking Individual (Vista previa de las 44 filas) */}
                    {(evaluation?.report_config?.show_ranking_table !== false) && (
                      <div className="panel" style={{ padding: "20px 24px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 8 }}>
                          <div>
                            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0 }}>
                              Ranking Individual y Desempeño Histórico (2023-2025)
                            </h3>
                            <span className="muted" style={{ fontSize: "0.75rem" }}>
                              Escala de semáforo: Verde (≥ {Number(executiveResults.thresholds?.high ?? 8.5).toFixed(1)} {evaluation?.report_config?.label_high || "Excede"}), Amarillo ({Number(executiveResults.thresholds?.medium ?? 7.0).toFixed(1)} - {(Number(executiveResults.thresholds?.high ?? 8.5) - 0.1).toFixed(1)} {evaluation?.report_config?.label_med || "Cumple"}), Rojo (≤ {(Number(executiveResults.thresholds?.medium ?? 7.0) - 0.1).toFixed(1)} {evaluation?.report_config?.label_low || "Requiere mejora"})
                            </span>
                          </div>
                          <div style={{ display: "flex", gap: 10, fontSize: "0.75rem" }}>
                            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                              <span style={{ width: 10, height: 10, background: "#dcfce7", border: "1px solid #16a34a", borderRadius: 2 }}></span>
                              ≥ {Number(executiveResults.thresholds?.high ?? 8.5).toFixed(2)}
                            </span>
                            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                              <span style={{ width: 10, height: 10, background: "#fef9c3", border: "1px solid #ca8a04", borderRadius: 2 }}></span>
                              {Number(executiveResults.thresholds?.medium ?? 7.0).toFixed(2)} - {(Number(executiveResults.thresholds?.high ?? 8.5) - 0.01).toFixed(2)}
                            </span>
                            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                              <span style={{ width: 10, height: 10, background: "#fee2e2", border: "1px solid #dc2626", borderRadius: 2 }}></span>
                              ≤ {(Number(executiveResults.thresholds?.medium ?? 7.0) - 0.01).toFixed(2)}
                            </span>
                          </div>
                        </div>

                        <div style={{ overflowX: "auto" }}>
                          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                            <thead>
                              <tr style={{ background: "#f1f5f9", textAlign: "left", borderBottom: "2px solid #cbd5e1" }}>
                                <th style={{ padding: "8px 10px", width: 50 }}>#</th>
                                <th style={{ padding: "8px 10px", width: 70 }}>Rol</th>
                                <th style={{ padding: "8px 10px", width: 130 }}>Línea</th>
                                <th style={{ padding: "8px 10px" }}>Colaborador</th>
                                {executiveResults.competencies.map((c) => (
                                  <th key={c.competency_id} style={{ padding: "8px 8px", textAlign: "center", minWidth: 90 }}>
                                    {c.competency_name.split(" ")[0]} ({c.weight_pct.toFixed(0)}%)
                                  </th>
                                ))}
                                <th style={{ padding: "8px 10px", textAlign: "center", minWidth: 70, background: "#e0f2fe" }}>Prom.</th>
                                <th style={{ padding: "8px 8px", textAlign: "center", minWidth: 60 }}>2023</th>
                                <th style={{ padding: "8px 8px", textAlign: "center", minWidth: 60 }}>2024</th>
                                <th style={{ padding: "8px 8px", textAlign: "center", minWidth: 60 }}>2025</th>
                              </tr>
                            </thead>
                            <tbody>
                              {executiveResults.participants_matrix.map((row, idx) => (
                                <tr
                                  key={row.participant_id}
                                  style={{
                                    borderBottom: "1px solid #e2e8f0",
                                    background: idx % 2 === 0 ? "#ffffff" : "#f8fafc",
                                  }}
                                >
                                  <td style={{ padding: "7px 10px", fontWeight: 700, color: "var(--muted)" }}>
                                    {idx + 1}
                                  </td>
                                  <td style={{ padding: "7px 10px", color: "var(--muted)" }}>
                                    {row.role || "SR"}
                                  </td>
                                  <td style={{ padding: "7px 10px", fontWeight: 600 }}>
                                    {row.business_line || "General"}
                                  </td>
                                  <td style={{ padding: "7px 10px", fontWeight: 700 }}>
                                    {row.participant_name}
                                  </td>
                                  {executiveResults.competencies.map((c) => {
                                    const val = row.net_scores[c.competency_name] ?? 0;
                                    const thH = Number(executiveResults.thresholds?.high ?? 8.5);
                                    const thM = Number(executiveResults.thresholds?.medium ?? 7.0);
                                    let bg = "#ffffff";
                                    let color = "#0f172a";
                                    if (val >= thH) {
                                      bg = "#dcfce7";
                                      color = "#15803d";
                                    } else if (val >= thM) {
                                      bg = "#fef9c3";
                                      color = "#854d0e";
                                    } else if (val > 0) {
                                      bg = "#fee2e2";
                                      color = "#b91c1c";
                                    }
                                    return (
                                      <td
                                        key={c.competency_id}
                                        style={{
                                          padding: "7px 8px",
                                          textAlign: "center",
                                          background: bg,
                                          color: color,
                                          fontWeight: 600,
                                        }}
                                      >
                                        {val.toFixed(2)}
                                      </td>
                                    );
                                  })}
                                <td
                                  style={{
                                    padding: "7px 10px",
                                    textAlign: "center",
                                    background: "#e0f2fe",
                                    fontWeight: 800,
                                    color: "#0369a1",
                                  }}
                                >
                                  {row.net_average.toFixed(2)}
                                </td>
                                <td style={{ padding: "7px 8px", textAlign: "center", fontSize: "0.75rem", color: "var(--muted)" }}>
                                  {row.performance_history?.["2023"] || "#N/D"}
                                </td>
                                <td style={{ padding: "7px 8px", textAlign: "center", fontSize: "0.75rem", color: "var(--muted)" }}>
                                  {row.performance_history?.["2024"] || "#N/D"}
                                </td>
                                <td style={{ padding: "7px 8px", textAlign: "center", fontSize: "0.75rem", color: "var(--muted)" }}>
                                  {row.performance_history?.["2025"] || "#N/D"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </section>
      {showReportConfigModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15, 23, 42, 0.7)",
            backdropFilter: "blur(6px)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "16px",
          }}
        >
          <div
            style={{
              background: "#ffffff",
              borderRadius: "16px",
              width: "100%",
              maxWidth: "840px",
              maxHeight: "92vh",
              display: "flex",
              flexDirection: "column",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
              overflow: "hidden",
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: "20px 24px",
                borderBottom: "1px solid #e2e8f0",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background: "#f8fafc",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: "10px",
                    background: "rgba(0,133,124,0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#00857c",
                  }}
                >
                  <Settings size={22} />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 800, color: "#0f172a" }}>
                    Configuración del Informe Ejecutivo & Salida
                  </h3>
                  <p style={{ margin: 0, fontSize: "0.8rem", color: "#64748b" }}>
                    Personaliza logotipos, nombres institucionales, textos de introducción y umbrales de semáforo para pantalla y PDF.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowReportConfigModal(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "#64748b",
                  padding: 6,
                  borderRadius: 6,
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Navigation Tabs */}
            <div
              style={{
                display: "flex",
                borderBottom: "1px solid #e2e8f0",
                background: "#ffffff",
                padding: "0 24px",
                gap: 8,
              }}
            >
              {[
                { id: "branding", label: "Logotipos y Marca", icon: <ImageIcon size={16} /> },
                { id: "content", label: "Títulos y Textos", icon: <FileText size={16} /> },
                { id: "thresholds", label: "Semáforo y Umbrales", icon: <Sliders size={16} /> },
                { id: "display", label: "Salida en Pantalla", icon: <LayoutGrid size={16} /> },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setConfigTab(tab.id as any)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "12px 16px",
                    fontSize: "0.85rem",
                    fontWeight: 700,
                    background: "none",
                    border: "none",
                    borderBottom: configTab === tab.id ? "3px solid #00857c" : "3px solid transparent",
                    color: configTab === tab.id ? "#00857c" : "#64748b",
                    cursor: "pointer",
                  }}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Modal Body */}
            <div style={{ padding: "24px", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: 20 }}>
              {configTab === "branding" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                  {/* Logo Cliente */}
                  <div style={{ background: "#f8fafc", padding: "18px 20px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                      <div>
                        <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "#0f172a" }}>
                          Logo del Cliente / Empresa Evaluada
                        </h4>
                        <p style={{ margin: "2px 0 0 0", fontSize: "0.78rem", color: "#64748b" }}>
                          Aparece en la portada principal y en la esquina superior izquierda de todas las páginas del reporte PDF y en la pantalla.
                        </p>
                      </div>
                      {clientLogoUrl && (
                        <button
                          type="button"
                          onClick={() => setClientLogoUrl("")}
                          style={{
                            background: "#fee2e2",
                            color: "#dc2626",
                            border: "none",
                            borderRadius: "6px",
                            padding: "4px 10px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                            cursor: "pointer",
                          }}
                        >
                          Quitar Logo (Usar predeterminado)
                        </button>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
                      <div
                        style={{
                          width: 160,
                          height: 80,
                          borderRadius: "8px",
                          border: "2px dashed #cbd5e1",
                          background: "#ffffff",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          overflow: "hidden",
                          padding: 6,
                        }}
                      >
                        {clientLogoUrl ? (
                          <img src={clientLogoUrl} alt="Preview Cliente" style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }} />
                        ) : (
                          <span style={{ fontSize: "0.72rem", color: "#94a3b8", textAlign: "center" }}>
                            Isotipo Vectorial MSD (Predeterminado)
                          </span>
                        )}
                      </div>

                      <div style={{ flex: 1, minWidth: 220, display: "flex", flexDirection: "column", gap: 8 }}>
                        <label
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: 8,
                            background: "#00857c",
                            color: "#ffffff",
                            padding: "8px 14px",
                            borderRadius: "8px",
                            fontSize: "0.82rem",
                            fontWeight: 700,
                            cursor: "pointer",
                            width: "fit-content",
                          }}
                        >
                          <Upload size={16} />
                          Subir Imagen de Logo
                          <input
                            type="file"
                            accept="image/*"
                            style={{ display: "none" }}
                            onChange={(e) => handleLogoFileUpload(e, "client")}
                          />
                        </label>
                        <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                          Formatos recomendados: PNG o JPG con fondo transparente o blanco (máx. 5 MB).
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Logo Consultora */}
                  <div style={{ background: "#f8fafc", padding: "18px 20px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                      <div>
                        <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "#0f172a" }}>
                          Logo de la Consultora / RRHH Emisor
                        </h4>
                        <p style={{ margin: "2px 0 0 0", fontSize: "0.78rem", color: "#64748b" }}>
                          Aparece en el pie de página inferior derecho de cada página del PDF y en el encabezado corporativo.
                        </p>
                      </div>
                      {consultantLogoUrl && (
                        <button
                          type="button"
                          onClick={() => setConsultantLogoUrl("")}
                          style={{
                            background: "#fee2e2",
                            color: "#dc2626",
                            border: "none",
                            borderRadius: "6px",
                            padding: "4px 10px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                            cursor: "pointer",
                          }}
                        >
                          Quitar Logo (Usar predeterminado)
                        </button>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
                      <div
                        style={{
                          width: 160,
                          height: 80,
                          borderRadius: "8px",
                          border: "2px dashed #cbd5e1",
                          background: "#ffffff",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          overflow: "hidden",
                          padding: 6,
                        }}
                      >
                        {consultantLogoUrl ? (
                          <img src={consultantLogoUrl} alt="Preview Consultor" style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }} />
                        ) : (
                          <span style={{ fontSize: "0.72rem", color: "#94a3b8", textAlign: "center" }}>
                            abc&co (Predeterminado)
                          </span>
                        )}
                      </div>

                      <div style={{ flex: 1, minWidth: 220, display: "flex", flexDirection: "column", gap: 8 }}>
                        <label
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: 8,
                            background: "#475569",
                            color: "#ffffff",
                            padding: "8px 14px",
                            borderRadius: "8px",
                            fontSize: "0.82rem",
                            fontWeight: 700,
                            cursor: "pointer",
                            width: "fit-content",
                          }}
                        >
                          <Upload size={16} />
                          Subir Imagen de Logo
                          <input
                            type="file"
                            accept="image/*"
                            style={{ display: "none" }}
                            onChange={(e) => handleLogoFileUpload(e, "consultant")}
                          />
                        </label>
                        <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                          Formatos recomendados: PNG horizontal o JPG (máx. 5 MB).
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {configTab === "content" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                    <div>
                      <label style={{ fontSize: "0.78rem", fontWeight: 700, color: "#334155", display: "block", marginBottom: 4 }}>
                        Nombre de la Empresa Cliente:
                      </label>
                      <input
                        type="text"
                        className="input"
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        placeholder="Ej. MSD Argentina"
                        style={{ width: "100%", fontSize: "0.85rem" }}
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: "0.78rem", fontWeight: 700, color: "#334155", display: "block", marginBottom: 4 }}>
                        Nombre de la Consultora:
                      </label>
                      <input
                        type="text"
                        className="input"
                        value={consultantName}
                        onChange={(e) => setConsultantName(e.target.value)}
                        placeholder="Ej. abc&co - Coaching & Consulting"
                        style={{ width: "100%", fontSize: "0.85rem" }}
                      />
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: "0.78rem", fontWeight: 700, color: "#334155", display: "block", marginBottom: 4 }}>
                      Título Superior de Encabezado (Header en páginas):
                    </label>
                    <input
                      type="text"
                      className="input"
                      value={headerTitle}
                      onChange={(e) => setHeaderTitle(e.target.value)}
                      placeholder="Reporte Grupal - Evaluación 360°"
                      style={{ width: "100%", fontSize: "0.85rem" }}
                    />
                  </div>

                  <div style={{ background: "#f8fafc", padding: "14px 16px", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
                    <span style={{ fontSize: "0.82rem", fontWeight: 800, color: "#0f172a", display: "block", marginBottom: 10 }}>
                      Portada (Página 1 del PDF)
                    </span>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 10 }}>
                      <div>
                        <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>Título L1</label>
                        <input
                          type="text"
                          className="input"
                          value={coverTitle1}
                          onChange={(e) => setCoverTitle1(e.target.value)}
                          style={{ width: "100%", fontSize: "0.82rem" }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>Título L2</label>
                        <input
                          type="text"
                          className="input"
                          value={coverTitle2}
                          onChange={(e) => setCoverTitle2(e.target.value)}
                          style={{ width: "100%", fontSize: "0.82rem" }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>Título L3 (Destacado)</label>
                        <input
                          type="text"
                          className="input"
                          value={coverTitle3}
                          onChange={(e) => setCoverTitle3(e.target.value)}
                          style={{ width: "100%", fontSize: "0.82rem" }}
                        />
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <div>
                        <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>Subtítulo L1</label>
                        <input
                          type="text"
                          className="input"
                          value={coverSub1}
                          onChange={(e) => setCoverSub1(e.target.value)}
                          style={{ width: "100%", fontSize: "0.82rem" }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: "0.72rem", color: "#64748b", display: "block", marginBottom: 2 }}>Subtítulo L2 / Área</label>
                        <input
                          type="text"
                          className="input"
                          value={coverSub2}
                          onChange={(e) => setCoverSub2(e.target.value)}
                          style={{ width: "100%", fontSize: "0.82rem" }}
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: "0.78rem", fontWeight: 700, color: "#334155", display: "block", marginBottom: 4 }}>
                      Introducción (Párrafo 1):
                    </label>
                    <textarea
                      className="input"
                      rows={2}
                      value={introP1}
                      onChange={(e) => setIntroP1(e.target.value)}
                      placeholder="En el contexto del proceso de transformación..."
                      style={{ width: "100%", fontSize: "0.82rem", lineHeight: 1.4 }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: "0.78rem", fontWeight: 700, color: "#334155", display: "block", marginBottom: 4 }}>
                      Objetivo Principal del Reporte:
                    </label>
                    <textarea
                      className="input"
                      rows={2}
                      value={objectivesMain}
                      onChange={(e) => setObjectivesMain(e.target.value)}
                      placeholder="Evaluar el nivel de desarrollo y homogeneidad de las competencias..."
                      style={{ width: "100%", fontSize: "0.82rem", lineHeight: 1.4 }}
                    />
                  </div>
                </div>
              )}

              {configTab === "thresholds" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                  <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", padding: "14px 18px", borderRadius: "10px" }}>
                    <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#166534", display: "block", marginBottom: 4 }}>
                      Semáforo de Rendimiento Corporativo (Escala 1 a 10)
                    </span>
                    <p style={{ margin: 0, fontSize: "0.78rem", color: "#15803d" }}>
                      Ajuste los valores de corte numérico. Las celdas de las matrices en pantalla y en las 29 páginas del PDF se colorearán automáticamente según estos límites.
                    </p>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
                    {/* Nivel Alto */}
                    <div style={{ background: "#f8fafc", border: "2px solid #22c55e", padding: "16px", borderRadius: "12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                        <span style={{ width: 14, height: 14, borderRadius: "50%", background: "#22c55e" }}></span>
                        <span style={{ fontSize: "0.9rem", fontWeight: 800, color: "#15803d" }}>Nivel Alto (Verde)</span>
                      </div>
                      <div style={{ marginBottom: 10 }}>
                        <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block", marginBottom: 3 }}>
                          Puntaje Mínimo (≥)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          min="1"
                          max="10"
                          className="input"
                          value={thHigh}
                          onChange={(e) => setThHigh(parseFloat(e.target.value) || 0)}
                          style={{ width: "100%", fontWeight: 700, fontSize: "1rem" }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block", marginBottom: 3 }}>
                          Etiqueta
                        </label>
                        <input
                          type="text"
                          className="input"
                          value={labelHigh}
                          onChange={(e) => setLabelHigh(e.target.value)}
                          style={{ width: "100%", fontSize: "0.82rem" }}
                        />
                      </div>
                    </div>

                    {/* Nivel Medio */}
                    <div style={{ background: "#f8fafc", border: "2px solid #eab308", padding: "16px", borderRadius: "12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                        <span style={{ width: 14, height: 14, borderRadius: "50%", background: "#eab308" }}></span>
                        <span style={{ fontSize: "0.9rem", fontWeight: 800, color: "#854d0e" }}>Nivel Medio (Amarillo)</span>
                      </div>
                      <div style={{ marginBottom: 10 }}>
                        <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block", marginBottom: 3 }}>
                          Puntaje Mínimo (≥)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          min="1"
                          max="10"
                          className="input"
                          value={thMed}
                          onChange={(e) => setThMed(parseFloat(e.target.value) || 0)}
                          style={{ width: "100%", fontWeight: 700, fontSize: "1rem" }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block", marginBottom: 3 }}>
                          Etiqueta
                        </label>
                        <input
                          type="text"
                          className="input"
                          value={labelMed}
                          onChange={(e) => setLabelMed(e.target.value)}
                          style={{ width: "100%", fontSize: "0.82rem" }}
                        />
                      </div>
                    </div>

                    {/* Nivel Bajo */}
                    <div style={{ background: "#f8fafc", border: "2px solid #ef4444", padding: "16px", borderRadius: "12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                        <span style={{ width: 14, height: 14, borderRadius: "50%", background: "#ef4444" }}></span>
                        <span style={{ fontSize: "0.9rem", fontWeight: 800, color: "#b91c1c" }}>Nivel Bajo (Rojo)</span>
                      </div>
                      <div style={{ marginBottom: 10 }}>
                        <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block", marginBottom: 3 }}>
                          Rango Automático
                        </label>
                        <div
                          style={{
                            height: 38,
                            display: "flex",
                            alignItems: "center",
                            padding: "0 12px",
                            background: "#fee2e2",
                            color: "#b91c1c",
                            borderRadius: 6,
                            fontWeight: 700,
                            fontSize: "0.9rem",
                          }}
                        >
                          &lt; {thMed.toFixed(1)}
                        </div>
                      </div>
                      <div>
                        <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block", marginBottom: 3 }}>
                          Etiqueta
                        </label>
                        <input
                          type="text"
                          className="input"
                          value={labelLow}
                          onChange={(e) => setLabelLow(e.target.value)}
                          style={{ width: "100%", fontSize: "0.82rem" }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {configTab === "display" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
                    Secciones visibles en la vista de pantalla:
                  </span>

                  <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", background: "#f8fafc", padding: "12px 14px", borderRadius: 8, border: "1px solid #e2e8f0" }}>
                    <input
                      type="checkbox"
                      checked={showPicosAlert}
                      onChange={(e) => setShowPicosAlert(e.target.checked)}
                      style={{ width: 18, height: 18 }}
                    />
                    <div>
                      <strong style={{ fontSize: "0.85rem", display: "block" }}>Alertas de Picos en Evaluaciones (Outliers)</strong>
                      <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Muestra las advertencias cuando hay discrepancias significativas entre evaluadores.</span>
                    </div>
                  </label>

                  <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", background: "#f8fafc", padding: "12px 14px", borderRadius: 8, border: "1px solid #e2e8f0" }}>
                    <input
                      type="checkbox"
                      checked={showInsightsSection}
                      onChange={(e) => setShowInsightsSection(e.target.checked)}
                      style={{ width: 18, height: 18 }}
                    />
                    <div>
                      <strong style={{ fontSize: "0.85rem", display: "block" }}>Principales Hallazgos y Análisis Estratégico</strong>
                      <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Muestra las viñetas analíticas automáticas sobre consistencia y dispersión.</span>
                    </div>
                  </label>

                  <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", background: "#f8fafc", padding: "12px 14px", borderRadius: 8, border: "1px solid #e2e8f0" }}>
                    <input
                      type="checkbox"
                      checked={showRankingTable}
                      onChange={(e) => setShowRankingTable(e.target.checked)}
                      style={{ width: 18, height: 18 }}
                    />
                    <div>
                      <strong style={{ fontSize: "0.85rem", display: "block" }}>Tabla de Ranking Individual y Desempeño Histórico</strong>
                      <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Muestra la matriz completa con colores de semáforo para cada colaborador.</span>
                    </div>
                  </label>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div
              style={{
                padding: "16px 24px",
                borderTop: "1px solid #e2e8f0",
                background: "#f8fafc",
                display: "flex",
                justifyContent: "flex-end",
                alignItems: "center",
                gap: 12,
              }}
            >
              <button
                type="button"
                onClick={() => setShowReportConfigModal(false)}
                className="button secondary"
                style={{ padding: "8px 16px", fontSize: "0.85rem" }}
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSaveReportConfig}
                disabled={savingReportConfig}
                className="button primary"
                style={{
                  background: "#00857c",
                  color: "#ffffff",
                  padding: "8px 20px",
                  fontSize: "0.85rem",
                  fontWeight: 800,
                  borderRadius: "8px",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <Save size={16} />
                {savingReportConfig ? "Guardando..." : "Guardar y Aplicar Configuración"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
