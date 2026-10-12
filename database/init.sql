CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. COMPANIES
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(160) NOT NULL,
    domain VARCHAR(160),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. USERS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(160) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(40) NOT NULL DEFAULT 'admin',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, email)
);

-- 3. EVALUATIONS
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'draft',
    assessment_type VARCHAR(60) DEFAULT 'individual_contributor',
    client_logo_url VARCHAR(500),
    consultant_logo_url VARCHAR(500),
    scale_type VARCHAR(50) DEFAULT 'numeric_1_10',
    score_thresholds JSONB DEFAULT '{"high": 8.5, "medium": 7.0}'::jsonb,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. COMPETENCY BANK
CREATE TABLE competency_bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. COMPETENCIES
CREATE TABLE competencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    competency_bank_id UUID REFERENCES competency_bank(id) ON DELETE SET NULL,
    name VARCHAR(160) NOT NULL,
    description TEXT,
    weight NUMERIC(6, 4) NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 6. QUESTION BANK
CREATE TABLE question_bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    competency_bank_id UUID REFERENCES competency_bank(id) ON DELETE SET NULL,
    competency_name VARCHAR(160) NOT NULL,
    text TEXT NOT NULL,
    text_self TEXT,
    text_evaluator TEXT,
    tag_self VARCHAR(100),
    tag_evaluator VARCHAR(100),
    question_type VARCHAR(50) NOT NULL DEFAULT 'numeric_1_10',
    options JSONB,
    is_evaluative BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. QUESTIONS
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    competency_id UUID NOT NULL REFERENCES competencies(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    text_self TEXT,
    text_evaluator TEXT,
    tag_self VARCHAR(100),
    tag_evaluator VARCHAR(100),
    position INTEGER NOT NULL DEFAULT 0,
    question_type VARCHAR(50) NOT NULL DEFAULT 'numeric_1_10',
    options JSONB,
    is_evaluative BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 8. PARTICIPANTS
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(160) NOT NULL,
    role VARCHAR(120),
    business_line VARCHAR(120),
    performance_history JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, evaluation_id, email)
);

-- 9. EVALUATOR ASSIGNMENTS
CREATE TABLE evaluator_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    evaluatee_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    evaluator_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    relationship VARCHAR(60) NOT NULL DEFAULT 'peer',
    weight NUMERIC(6, 4) NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, evaluation_id, evaluatee_id, evaluator_id)
);

-- 10. SURVEY TOKENS
CREATE TABLE survey_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    assignment_id UUID NOT NULL REFERENCES evaluator_assignments(id) ON DELETE CASCADE,
    token VARCHAR(120) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 11. RESPONSES
CREATE TABLE responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    assignment_id UUID NOT NULL REFERENCES evaluator_assignments(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    score INTEGER CHECK (score BETWEEN 1 AND 10), -- NULLABLE para soportar cualitativas y "No observado"
    selected_option VARCHAR(200),
    selected_options JSONB,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, assignment_id, question_id)
);

-- 12. AI REPORTS
CREATE TABLE ai_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    participant_id UUID REFERENCES participants(id) ON DELETE CASCADE,
    report_type VARCHAR(40) NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- INDICES
CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_evaluations_company ON evaluations(company_id);
CREATE INDEX idx_competencies_evaluation ON competencies(company_id, evaluation_id);
CREATE INDEX idx_questions_evaluation ON questions(company_id, evaluation_id);
CREATE INDEX idx_participants_evaluation ON participants(company_id, evaluation_id);
CREATE INDEX idx_assignments_evaluation ON evaluator_assignments(company_id, evaluation_id);
CREATE INDEX idx_tokens_token ON survey_tokens(token);
CREATE INDEX idx_responses_assignment ON responses(company_id, assignment_id);
CREATE INDEX idx_reports_evaluation ON ai_reports(company_id, evaluation_id);


-- SEMILLAS (SEED DATA) GLOBAL (company_id = NULL)
-- Competency Bank
INSERT INTO competency_bank (id, name, description, company_id) VALUES
('c0000000-0000-0000-0000-000000000001', 'Comunicación', 'Habilidad para transmitir ideas y escuchar de manera efectiva.', NULL),
('c0000000-0000-0000-0000-000000000002', 'Trabajo en Equipo', 'Colaborar con otros de manera proactiva para lograr metas comunes.', NULL),
('c0000000-0000-0000-0000-000000000003', 'Liderazgo', 'Capacidad para guiar, empoderar y motivar a otros miembros del equipo.', NULL),
('c0000000-0000-0000-0000-000000000004', 'Resolución de Problemas', 'Identificar dificultades y proponer soluciones viables y oportunas.', NULL),
('c0000000-0000-0000-0000-000000000005', 'Orientación al Cliente', 'Alinear acciones para satisfacer las necesidades de clientes internos y externos.', NULL);

-- Question Bank
INSERT INTO question_bank (competency_bank_id, competency_name, text, text_self, text_evaluator, tag_self, tag_evaluator, question_type, options, is_evaluative, company_id) VALUES
-- Comunicación
('c0000000-0000-0000-0000-000000000001', 'Comunicación', '¿Expresa sus ideas de forma clara y estructurada en reuniones?', '¿Expreso mis ideas de forma clara y estructurada en reuniones?', '¿Expresa sus ideas de forma clara y estructurada en reuniones?', 'P1 Autoevaluado', 'P1B Evaluador', 'numeric_1_10', NULL, true, NULL),
('c0000000-0000-0000-0000-000000000001', 'Comunicación', '¿Escucha activamente y respeta los puntos de vista de los demás?', '¿Escucho activamente y respeto los puntos de vista de los demás?', '¿Escucha activamente y respeta los puntos de vista de los demás?', 'P2 Autoevaluado', 'P2B Evaluador', 'numeric_1_10', NULL, true, NULL),
('c0000000-0000-0000-0000-000000000001', 'Comunicación', '¿Mantiene informados a sus compañeros sobre el avance de sus tareas?', '¿Mantengo informados a mis compañeros sobre el avance de mis tareas?', '¿Mantiene informados a sus compañeros sobre el avance de sus tareas?', 'P3 Autoevaluado', 'P3B Evaluador', 'dicotomic', NULL, true, NULL),

-- Trabajo en Equipo
('c0000000-0000-0000-0000-000000000002', 'Trabajo en Equipo', '¿Colabora activamente en tareas grupales aunque no sean de su responsabilidad directa?', '¿Colaboro activamente en tareas grupales aunque no sean de mi responsabilidad directa?', '¿Colabora activamente en tareas grupales aunque no sean de su responsabilidad directa?', 'P4 Autoevaluado', 'P4B Evaluador', 'numeric_1_10', NULL, true, NULL),
('c0000000-0000-0000-0000-000000000002', 'Trabajo en Equipo', '¿Promueve un ambiente de trabajo positivo y de apoyo mutuo?', '¿Promuevo un ambiente de trabajo positivo y de apoyo mutuo?', '¿Promueve un ambiente de trabajo positivo y de apoyo mutuo?', 'P5 Autoevaluado', 'P5B Evaluador', 'numeric_1_10', NULL, true, NULL),
('c0000000-0000-0000-0000-000000000002', 'Trabajo en Equipo', '¿Cómo evalúas su disposición a recibir retroalimentación constructiva?', '¿Cómo evalúo mi disposición a recibir retroalimentación constructiva?', '¿Cómo evalúas la disposición del colaborador a recibir retroalimentación constructiva?', 'P6 Autoevaluado', 'P6B Evaluador', 'likert', '["Muy en desacuerdo", "En desacuerdo", "Neutral", "De acuerdo", "Muy de acuerdo"]', true, NULL),

-- Liderazgo
('c0000000-0000-0000-0000-000000000003', 'Liderazgo', '¿Asume la responsabilidad del resultado de los proyectos del equipo?', '¿Asumo la responsabilidad del resultado de los proyectos del equipo?', '¿Asume la responsabilidad del resultado de los proyectos del equipo?', 'P7 Autoevaluado', 'P7B Evaluador', 'numeric_1_10', NULL, true, NULL),
('c0000000-0000-0000-0000-000000000003', 'Liderazgo', '¿Delega tareas de manera efectiva considerando las fortalezas de cada persona?', '¿Delego tareas de manera efectiva considerando las fortalezas de cada persona?', '¿Delega tareas de manera efectiva considerando las fortalezas de cada persona?', 'P8 Autoevaluado', 'P8B Evaluador', 'numeric_1_10', NULL, true, NULL),
('c0000000-0000-0000-0000-000000000003', 'Liderazgo', '¿Brinda retroalimentación constructiva para ayudar al crecimiento de los demás?', '¿Brindo retroalimentación constructiva para ayudar al crecimiento de los demás?', '¿Brinda retroalimentación constructiva para ayudar al crecimiento de los demás?', 'P9 Autoevaluado', 'P9B Evaluador', 'numeric_1_10', NULL, true, NULL),

-- Resolución de Problemas
('c0000000-0000-0000-0000-000000000004', 'Resolución de Problemas', '¿Analiza los problemas de manera lógica identificando sus causas raíz?', '¿Analizo los problemas de manera lógica identificando sus causas raíz?', '¿Analiza los problemas de manera lógica identificando sus causas raíz?', 'P10 Autoevaluado', 'P10B Evaluador', 'numeric_1_10', NULL, true, NULL),
('c0000000-0000-0000-0000-000000000004', 'Resolución de Problemas', '¿Propone soluciones innovadoras ante situaciones críticas?', '¿Propongo soluciones innovadoras ante situaciones críticas?', '¿Propone soluciones innovadoras ante situaciones críticas?', 'P11 Autoevaluado', 'P11B Evaluador', 'numeric_1_10', NULL, true, NULL),

-- Orientación al Cliente
('c0000000-0000-0000-0000-000000000005', 'Orientación al Cliente', '¿Se esfuerza por comprender y resolver las necesidades de los clientes?', '¿Me esfuerzo por comprender y resolver las necesidades de los clientes?', '¿Se esfuerza por comprender y resolver las necesidades de los clientes?', 'P12 Autoevaluado', 'P12B Evaluador', 'numeric_1_10', NULL, true, NULL),
('c0000000-0000-0000-0000-000000000005', 'Orientación al Cliente', '¿Muestra empatía y paciencia al atender consultas o reclamos?', '¿Muestro empatía y paciencia al atender consultas o reclamos?', '¿Muestra empatía y paciencia al atender consultas o reclamos?', 'P13 Autoevaluado', 'P13B Evaluador', 'numeric_1_10', NULL, true, NULL);
