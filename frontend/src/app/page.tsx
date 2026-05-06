"use client";

import { BarChart3, LogOut, Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, API_URL, ApiError, Evaluation } from "@/lib/api";

type Mode = "login" | "register";

export default function HomePage() {
  const [token, setToken] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("login");
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [apiStatus, setApiStatus] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("rrhh_token");
    if (saved) {
      setToken(saved);
    }
    function handleInvalidAuth() {
      setToken(null);
      setEvaluations([]);
      setMessage("Sesion vencida. Inicia sesion nuevamente.");
    }
    window.addEventListener("rrhh_auth_invalid", handleInvalidAuth);
    return () => window.removeEventListener("rrhh_auth_invalid", handleInvalidAuth);
  }, []);

  useEffect(() => {
    async function checkApi() {
      try {
        await api<{ status: string }>("/health");
        setApiStatus(`API conectada: ${API_URL}`);
      } catch (error) {
        setApiStatus(`API no accesible: ${API_URL}`);
      }
    }
    void checkApi();
  }, []);

  useEffect(() => {
    if (token) {
      void loadEvaluations(token);
    }
  }, [token]);

  async function loadEvaluations(authToken = token) {
    if (!authToken) return;
    setLoading(true);
    setMessage("");
    try {
      setEvaluations(await api<Evaluation[]>("/evaluations", {}, authToken));
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setToken(null);
        setEvaluations([]);
      }
      setMessage(error instanceof Error ? error.message : "No se pudieron cargar evaluaciones");
    } finally {
      setLoading(false);
    }
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    const data = new FormData(event.currentTarget);
    const path = mode === "login" ? "/auth/login" : "/auth/register";
    const payload =
      mode === "login"
        ? {
            email: data.get("email"),
            password: data.get("password"),
          }
        : {
            company_name: data.get("company_name"),
            company_domain: data.get("company_domain"),
            full_name: data.get("full_name"),
            email: data.get("email"),
            password: data.get("password"),
          };

    try {
      const result = await api<{ access_token: string }>(path, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      localStorage.setItem("rrhh_token", result.access_token);
      setToken(result.access_token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo autenticar");
    } finally {
      setLoading(false);
    }
  }

  async function createEvaluation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setLoading(true);
    setMessage("");
    const data = new FormData(event.currentTarget);
    try {
      await api<Evaluation>(
        "/evaluations",
        {
          method: "POST",
          body: JSON.stringify({
            title: data.get("title"),
            description: data.get("description"),
          }),
        },
        token,
      );
      event.currentTarget.reset();
      await loadEvaluations(token);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setToken(null);
        setEvaluations([]);
      }
      setMessage(error instanceof Error ? error.message : "No se pudo crear la evaluacion");
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("rrhh_token");
    setToken(null);
    setEvaluations([]);
  }

  if (!token) {
    return (
      <main className="auth-page">
        <section className="panel auth-card">
          <div className="brand" style={{ marginBottom: 18 }}>
            <span className="brand-mark">360</span>
            <span>RRHH 360 AI</span>
          </div>
          {apiStatus && <p className={apiStatus.includes("conectada") ? "success" : "error"}>{apiStatus}</p>}
          <div className="tabs" style={{ marginBottom: 18 }}>
            <button
              className={`tab ${mode === "login" ? "active" : ""}`}
              onClick={() => setMode("login")}
              type="button"
            >
              Login
            </button>
            <button
              className={`tab ${mode === "register" ? "active" : ""}`}
              onClick={() => setMode("register")}
              type="button"
            >
              Registro
            </button>
          </div>
          <form className="form" onSubmit={handleAuth}>
            {mode === "register" && (
              <>
                <div className="field">
                  <label>Empresa</label>
                  <input className="input" name="company_name" required />
                </div>
                <div className="field">
                  <label>Dominio</label>
                  <input className="input" name="company_domain" placeholder="empresa.com" />
                </div>
                <div className="field">
                  <label>Nombre</label>
                  <input className="input" name="full_name" required />
                </div>
              </>
            )}
            <div className="field">
              <label>Email</label>
              <input className="input" name="email" required type="email" />
            </div>
            <div className="field">
              <label>Password</label>
              <input className="input" minLength={8} name="password" required type="password" />
            </div>
            {message && <p className="error">{message}</p>}
            <button className="button" disabled={loading} type="submit">
              {loading ? <RefreshCw size={16} /> : null}
              {mode === "login" ? "Entrar" : "Crear cuenta"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">360</span>
          <span>RRHH 360 AI</span>
        </div>
        <button className="button secondary" onClick={logout} type="button">
          <LogOut size={16} />
          Salir
        </button>
      </header>
      <section className="content">
        <div className="page-title">
          <div>
            <h1>Evaluaciones</h1>
            <p className="muted">Panel operativo para crear y medir evaluaciones 360.</p>
          </div>
          <button className="button secondary" onClick={() => loadEvaluations()} type="button">
            <RefreshCw size={16} />
            Actualizar
          </button>
        </div>

        <div className="grid two">
          <section className="panel">
            <h2>Nueva evaluacion</h2>
            <form className="form" onSubmit={createEvaluation} style={{ marginTop: 14 }}>
              <div className="field">
                <label>Titulo</label>
                <input className="input" name="title" required />
              </div>
              <div className="field">
                <label>Descripcion</label>
                <textarea className="textarea" name="description" />
              </div>
              <button className="button" disabled={loading} type="submit">
                <Plus size={16} />
                Crear
              </button>
            </form>
            {message && <p className="error">{message}</p>}
          </section>

          <section className="panel">
            <div className="row">
              <h2>Activas</h2>
              <BarChart3 size={22} />
            </div>
            <div className="list">
              {evaluations.map((evaluation) => (
                <Link className="item" href={`/evaluations/${evaluation.id}`} key={evaluation.id}>
                  <strong>{evaluation.title}</strong>
                  <span className="muted">{evaluation.description || "Sin descripcion"}</span>
                  <span className="muted">Estado: {evaluation.status}</span>
                </Link>
              ))}
              {!evaluations.length && <p className="muted">Todavia no hay evaluaciones.</p>}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
