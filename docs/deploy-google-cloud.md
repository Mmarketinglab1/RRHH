# Deploy en Google Cloud sin Cloud SQL

Para bajar costo en el MVP, usamos Google Cloud solo para ejecutar la API y dejamos PostgreSQL en un proveedor externo serverless.

Arquitectura recomendada:

- Cloud Run: API FastAPI containerizada.
- Neon Postgres: base de datos PostgreSQL administrada externa.
- Secret Manager: `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`.
- Artifact Registry: imagen Docker del backend.
- Cloud Build: build y deploy repetible desde `cloudbuild.yaml`.

## Por que no Cloud SQL en el MVP

Cloud SQL es solido, pero para un MVP B2B temprano suele ser mas caro que la API misma porque la instancia queda provisionada. Para esta etapa conviene un Postgres serverless externo.

Decision simple: usar Neon para DB. Motivo: el sistema solo necesita PostgreSQL, no auth/storage/realtime de Supabase, y Neon ofrece Postgres serverless con plan gratuito y escala a cero cuando esta inactivo.

## 1. Crear base en Neon

1. Crear proyecto en Neon.
2. Crear una database, por ejemplo `evaluation360`.
3. Copiar el connection string pooled si esta disponible.
4. Debe quedar con este formato aproximado:

```text
postgresql+psycopg://USER:PASSWORD@HOST/evaluation360?sslmode=require
```

Importante: el backend usa SQLAlchemy con `psycopg`, por eso el prefijo debe ser `postgresql+psycopg://`.

## 2. Inicializar tablas

Ejecutar el SQL de [database/init.sql](../database/init.sql) contra Neon.

Opciones:

- Desde la consola SQL de Neon, pegando el contenido de `database/init.sql`.
- Desde una terminal con `psql`:

```bash
psql "postgresql://USER:PASSWORD@HOST/evaluation360?sslmode=require" -f database/init.sql
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
export DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST/evaluation360?sslmode=require"
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
printf "%s" "postgresql+psycopg://USER:PASSWORD@HOST/evaluation360?sslmode=require" \
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

## 9. Probar

```bash
SERVICE_URL="$(gcloud run services describe $SERVICE --region=$REGION --format='value(status.url)')"
curl "$SERVICE_URL/health"
```

Respuesta esperada:

```json
{"status":"ok"}
```

## Alternativa Supabase

Supabase tambien sirve si queres centralizar Auth, Storage o Realtime mas adelante. Para este MVP no lo necesitamos, por eso la decision mas simple es Neon + Cloud Run.

## Nota CTO

Dejamos `--allow-unauthenticated` porque la API maneja JWT y los endpoints publicos de encuesta necesitan acceso sin login. En produccion conviene agregar CORS por dominio, rate limiting y separar entornos `staging`/`production`.
