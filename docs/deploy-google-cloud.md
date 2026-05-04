# Deploy en Google Cloud

Arquitectura recomendada para el MVP:

- Cloud Run: API FastAPI containerizada.
- Cloud SQL PostgreSQL: base de datos multi-tenant.
- Secret Manager: `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`.
- Artifact Registry: imagen Docker del backend.
- Cloud Build: build y deploy repetible desde `cloudbuild.yaml`.

## 1. Variables

Reemplazar valores segun tu proyecto:

```bash
PROJECT_ID="tu-proyecto-gcp"
REGION="us-central1"
SERVICE="rrhh-api"
AR_REPO="rrhh"
DB_INSTANCE="rrhh-postgres"
DB_NAME="evaluation360"
DB_USER="rrhh_app"
DB_PASSWORD="usar-un-password-fuerte"
```

## 2. Habilitar APIs

```bash
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

## 3. Crear Artifact Registry

```bash
gcloud artifacts repositories create $AR_REPO \
  --repository-format=docker \
  --location=$REGION
```

## 4. Crear Cloud SQL PostgreSQL

```bash
gcloud sql instances create $DB_INSTANCE \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=$REGION

gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE

gcloud sql users create $DB_USER \
  --instance=$DB_INSTANCE \
  --password=$DB_PASSWORD
```

Para inicializar tablas, ejecutar `database/init.sql` contra Cloud SQL. La forma mas directa es usar Cloud SQL Auth Proxy local o Cloud Shell con `psql`.

## 5. Crear secretos

Obtener el connection name:

```bash
INSTANCE_CONNECTION_NAME="$(gcloud sql instances describe $DB_INSTANCE --format='value(connectionName)')"
```

Crear `DATABASE_URL` usando socket Unix de Cloud Run:

```bash
DATABASE_URL="postgresql+psycopg://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$INSTANCE_CONNECTION_NAME"

printf "%s" "$DATABASE_URL" | gcloud secrets create rrhh-database-url --data-file=-
printf "%s" "cambiar-por-un-jwt-secret-largo" | gcloud secrets create rrhh-jwt-secret --data-file=-
printf "%s" "sk-proj-tu-api-key" | gcloud secrets create rrhh-openai-api-key --data-file=-
```

Si ya existen, usar:

```bash
printf "%s" "$DATABASE_URL" | gcloud secrets versions add rrhh-database-url --data-file=-
```

## 6. Permisos para Cloud Build y Cloud Run

Cloud Build debe poder desplegar Cloud Run y usar Artifact Registry. En proyectos nuevos puede hacer falta:

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
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/secretmanager.secretAccessor"
```

## 7. Deploy

Desde la raiz del repo:

```bash
INSTANCE_CONNECTION_NAME="$(gcloud sql instances describe $DB_INSTANCE --format='value(connectionName)')"

gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions _REGION=$REGION,_SERVICE=$SERVICE,_AR_REPO=$AR_REPO,_INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME
```

## 8. Probar

```bash
SERVICE_URL="$(gcloud run services describe $SERVICE --region=$REGION --format='value(status.url)')"
curl "$SERVICE_URL/health"
```

La respuesta esperada:

```json
{"status":"ok"}
```

## Nota CTO

Para el MVP dejamos `--allow-unauthenticated` porque la API maneja JWT y los endpoints publicos de encuesta necesitan acceso sin login. En produccion conviene revisar CORS, rate limiting, dominios permitidos y politicas de seguridad por entorno.
