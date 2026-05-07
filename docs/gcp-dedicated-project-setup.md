# Dedicated Google Cloud Project Setup For Methodic

Date: 2026-05-06
Purpose: create a dedicated, credit-backed Google Cloud project for the Methodic hackathon demo.

Use this before deploying `methodic-demo` to Cloud Run.

## What We Are Creating

- One dedicated Google Cloud project
- One Artifact Registry Docker repository
- One BigQuery dataset: `methodic_demo`
- One Cloud Run runtime service account
- One Secret Manager secret for the Gemini API key
- One budget alert

We are not creating GKE, Redis, Firestore, or multi-region infrastructure for the first demo.

## Prerequisites

You need:

- access to the Google Cloud account that received the $500 hackathon credits
- `gcloud` authenticated locally
- permission to create projects or a project already created through the hackathon flow
- permission to link the project to the credit-backed billing account
- a Gemini API key or the configured Google AI/Gemini project access path

Check local auth:

```bash
gcloud auth list
gcloud config list
gcloud billing accounts list
```

If the hackathon credits require a console-created project, create it in the console first, then continue from "Configure Existing Project".

## Create A New Project

```bash
export PROJECT_ID="methodic-demo-$(date +%y%m%d)"
export PROJECT_NAME="Methodic Demo"
export REGION="us-central1"
export BILLING_ACCOUNT_ID="<your-billing-account-id>"

gcloud projects create "$PROJECT_ID" \
  --name="$PROJECT_NAME" \
  --set-as-default

gcloud billing projects link "$PROJECT_ID" \
  --billing-account="$BILLING_ACCOUNT_ID"

gcloud config set project "$PROJECT_ID"
```

Verify billing:

```bash
gcloud billing projects describe "$PROJECT_ID"
```

Do not proceed unless this shows the credit-backed billing account.

## Configure Existing Project

If the project already exists:

```bash
export PROJECT_ID="<existing-project-id>"
export REGION="us-central1"
gcloud config set project "$PROJECT_ID"
gcloud billing projects describe "$PROJECT_ID"
```

## Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  bigquery.googleapis.com \
  secretmanager.googleapis.com \
  generativelanguage.googleapis.com \
  aiplatform.googleapis.com
```

## Create Artifact Registry

```bash
gcloud artifacts repositories create methodic \
  --repository-format=docker \
  --location="$REGION" \
  --description="Methodic demo containers"
```

## Create BigQuery Dataset

```bash
bq --location="$REGION" mk --dataset "$PROJECT_ID:methodic_demo"
```

If it already exists, that is fine.

## Create Runtime Service Account

```bash
export RUNTIME_SA="methodic-demo-runner"
export RUNTIME_SA_EMAIL="$RUNTIME_SA@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create "$RUNTIME_SA" \
  --display-name="Methodic Cloud Run runtime"
```

Grant runtime permissions:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/bigquery.dataEditor"
```

This uses project-level BigQuery data editor for speed. After the demo works, tighten it to dataset-level access if time permits.

## Store Gemini API Key In Secret Manager

```bash
read -r -s -p "Gemini API key: " GEMINI_API_KEY
printf "\n"

printf "%s" "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
  --replication-policy=automatic \
  --data-file=-

gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

## Create Budget Alert

```bash
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT_ID" \
  --display-name="Methodic demo budget" \
  --budget-amount=400 \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

If the CLI budget command fails because of billing-account permissions, create the alert in the Cloud Console.

## Deploy Command Shape

Run from repo root after local tests pass:

```bash
export IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/methodic/methodic-demo:$(git rev-parse --short HEAD)"

docker build -t "$IMAGE" .
docker push "$IMAGE"

gcloud run deploy methodic-demo \
  --image="$IMAGE" \
  --region="$REGION" \
  --allow-unauthenticated \
  --service-account="$RUNTIME_SA_EMAIL" \
  --max-instances=1 \
  --min-instances=0 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=methodic_demo,BIGQUERY_DRY_RUN=false,METHODIC_MODEL=gemini-2.5-flash" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

The `--max-instances=1` flag is intentional while demo session state is stored in process memory.

## Smoke Checks

```bash
export SERVICE_URL="$(gcloud run services describe methodic-demo --region="$REGION" --format='value(status.url)')"

curl -fsS "$SERVICE_URL/health"
curl -fsS "$SERVICE_URL/.well-known/agent-card.json" | python3 -m json.tool
curl -fsS "$SERVICE_URL/static/demo.html" >/dev/null

curl -fsS -X POST "$SERVICE_URL/api/demo/run" | python3 -m json.tool
```

Then use the returned `study_id`:

```bash
export STUDY_ID="<returned-study-id>"
curl -fsS "$SERVICE_URL/api/demo/$STUDY_ID/status" | python3 -m json.tool
curl -fsS "$SERVICE_URL/api/demo/$STUDY_ID/events" | python3 -m json.tool
curl -fsS "$SERVICE_URL/api/demo/$STUDY_ID/coverage" | python3 -m json.tool
```

BigQuery proof:

```bash
bq query --use_legacy_sql=false \
  "SELECT * FROM \`$PROJECT_ID.methodic_demo.win_loss_responses\` ORDER BY exported_at DESC LIMIT 5"
```

## Stop Conditions

Pause deployment and fix locally if:

- `/health` fails
- the service logs show import errors
- demo status never leaves `running`
- events are empty
- MCP subprocess fails in Cloud Run
- BigQuery export reports errors
- model ID errors appear in logs

## References

- Google Cloud project creation: https://cloud.google.com/resource-manager/docs/creating-managing-projects
- `gcloud projects create`: https://cloud.google.com/sdk/gcloud/reference/projects/create
- Cloud Run deploy flags: https://cloud.google.com/sdk/gcloud/reference/run/deploy
- Cloud Run secrets: https://cloud.google.com/run/docs/configuring/services/secrets
- Billing budgets: https://cloud.google.com/sdk/gcloud/reference/billing/budgets/create
