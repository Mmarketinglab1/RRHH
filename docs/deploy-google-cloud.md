# Deploy en Google Cloud sin Cloud SQL

Para bajar costo en el MVP, usamos Google Cloud solo para ejecutar la API y dejamos PostgreSQL en un proveedor externo serverless.

Arquitectura recomendada:

- Cloud Run: API FastAPI containerizada.
- Supabase Postgres: base de datos PostgreSQL administrada externa.
- Secret Manager: `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`.
- Artifact Registry: imagen Docker del backend.
- Cloud Build: build y deploy repetible desde `cloudbuild.yaml`.

## Por que no Cloud SQL en el MVP

Cloud SQL es solido, pero para un MVP B2B temprano suele ser mas caro que la API misma porque la instancia queda provisionada. Para esta etapa conviene un Postgres serverless externo.

Decision simple: usar Supabase para DB. Motivo: ya te deja PostgreSQL administrado, consola SQL, backups basicos y la posibilidad de sumar Auth/Storage mas adelante si el producto lo necesita.

## 1. Crear base en Supabase

1. Crear un proyecto en Supabase.
2. Ir a `Project Settings` -> `Database`.
3. Copiar el connection string de Postgres.
4. Para Cloud Run, preferir el pooler en `Session mode` si esta disponible.
4. Debe quedar con este formato aproximado:

```text
postgresql+psycopg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require
```

Importante: Supabase suele mostrar el prefijo como `postgresql://`. Para este backend hay que usar `postgresql+psycopg://` porque SQLAlchemy esta configurado con `psycopg`.

## 2. Inicializar tablas

Ejecutar el SQL de [database/init.sql](../database/init.sql) contra Supabase.

Opciones:

- Desde `SQL Editor` de Supabase, pegando el contenido de `database/init.sql`.
- Desde una terminal con `psql`:

```bash
psql "postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require" -f database/init.sql
```

## 3. Variables de Google Cloud

```bash
PROJECT_ID="tu-proyecto-gcp"
REGION="us-central1"
SERVICE="rrhh-api"
AR_REPO="rrhh"
```

## Opcion rapida con Cloud Shell

Como en esta maquina local no esta instalado `gcloud`, el camino mas simple es usar Google Cloud Shell.

1. Abrir [Google Cloud Shell](https://shell.cloud.google.com/).
2. Clonar el repo:

```bash
git clone https://github.com/Mmarketinglab1/RRHH.git
cd RRHH
```

3. Exportar variables:

```bash
export PROJECT_ID="tu-proyecto-gcp-unico"
export BILLING_ACCOUNT_ID="XXXXXX-XXXXXX-XXXXXX"
export REGION="us-central1"
export DATABASE_URL="postgresql+psycopg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require"
export JWT_SECRET="usar-un-secret-largo"
export OPENAI_API_KEY="sk-proj-tu-api-key"
```

4. Ejecutar bootstrap:

```bash
bash scripts/gcp-bootstrap.sh
```

Si no sabes tu billing account:

```bash
gcloud billing accounts list
```

## 4. Habilitar APIs

```bash
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

## 5. Crear Artifact Registry

```bash
gcloud artifacts repositories create $AR_REPO \
  --repository-format=docker \
  --location=$REGION
```

## 6. Crear secretos

```bash
printf "%s" "postgresql+psycopg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require" \
  | gcloud secrets create rrhh-database-url --data-file=-

printf "%s" "cambiar-por-un-jwt-secret-largo" \
  | gcloud secrets create rrhh-jwt-secret --data-file=-

printf "%s" "sk-proj-tu-api-key" \
  | gcloud secrets create rrhh-openai-api-key --data-file=-
```

Si el secreto ya existe:

```bash
printf "%s" "nuevo-valor" | gcloud secrets versions add rrhh-database-url --data-file=-
```

## 7. Permisos

Cloud Build debe poder desplegar Cloud Run y escribir imagenes. El runtime de Cloud Run debe poder leer secretos.

```bash
PROJECT_NUMBER="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
CLOUD_BUILD_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"
RUNTIME_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/secretmanager.secretAccessor"
```

## 8. Deploy

Desde la raiz del repo:

```bash
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions _REGION=$REGION,_SERVICE=$SERVICE,_AR_REPO=$AR_REPO
```

El script `scripts/gcp-bootstrap.sh` tambien despliega el frontend con `cloudbuild.frontend.yaml`, usando la URL real de la API como `NEXT_PUBLIC_API_URL`.

## 9. Probar

```bash
SERVICE_URL="$(gcloud run services describe $SERVICE --region=$REGION --format='value(status.url)')"
curl "$SERVICE_URL/health"
```

Respuesta esperada:

```json
{"status":"ok"}
```

## Nota Supabase

Si usas el connection string directo en vez del pooler, tambien funciona, pero en Cloud Run el pooler ayuda a evitar exceso de conexiones cuando el servicio escala horizontalmente.

## Nota CTO

Dejamos `--allow-unauthenticated` porque la API maneja JWT y los endpoints publicos de encuesta necesitan acceso sin login. En produccion conviene agregar CORS por dominio, rate limiting y separar entornos `staging`/`production`.
