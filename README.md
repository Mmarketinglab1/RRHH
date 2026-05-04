# SaaS Evaluacion 360 con IA

MVP multi-tenant para evaluaciones 360 B2B.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Frontend: Next.js
- IA: OpenAI API
- Local: Docker Compose

## Correr localmente

1. Copiar variables:

```bash
cp .env.example .env
```

2. Levantar servicios:

```bash
docker compose up --build
```

3. Abrir API:

- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Deploy en Google Cloud

La guia de deploy esta en [docs/deploy-google-cloud.md](docs/deploy-google-cloud.md).
Para hacerlo desde Cloud Shell, usar [scripts/gcp-bootstrap.sh](scripts/gcp-bootstrap.sh).

La configuracion preparada usa:

- Cloud Run para el backend FastAPI.
- Cloud Run para el frontend Next.js.
- Supabase Postgres para datos multi-tenant, evitando Cloud SQL en el MVP.
- Secret Manager para credenciales y API keys.
- Artifact Registry + Cloud Build para build y deploy.

## Decisiones simples

- Multi-tenant: todos los recursos de negocio tienen `company_id`.
- Auth: JWT con `company_id` incluido en el usuario autenticado.
- Login: para este MVP, si un email existe en mas de una empresa se rechaza por ambiguedad; en produccion conviene usar subdominio o selector de empresa.
- Migraciones: para MVP se usa `database/init.sql` al crear el contenedor de Postgres.
- IA: si `OPENAI_API_KEY` no esta configurada, los servicios devuelven contenido deterministico de fallback para poder simular localmente.

## CSV de participantes

Columnas requeridas:

```csv
email,full_name,role
ana@acme.com,Ana Perez,Manager
leo@acme.com,Leo Gomez,Developer
```
