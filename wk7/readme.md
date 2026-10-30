# Pipeline Failure Explainer

An AI-powered application that helps data engineers troubleshoot failed Spark/Glue jobs by combining log analysis, Retrieval-Augmented Generation (RAG), and Gemini on Google Cloud Platform (GCP).

## 1. Project Overview

**Project Name:** GCP Pipeline Failure Explainer

**Core Idea:**

A web application that allows data engineers to enter a failed Spark/Glue job ID. The system automatically retrieves error logs from Cloud Logging, searches a historical failure knowledge base using RAG, and leverages Gemini to generate plain-English root cause explanations and actionable remediation suggestions.

**Problem It Solves:**

When troubleshooting Spark job failures, data engineers often switch between CloudWatch logs, Spark UI, and Step Functions execution history, manually comparing stack traces and metrics. This process is time-consuming and heavily dependent on individual experience.

Traditional monitoring tools are primarily reactive: they detect failures and generate alerts but rarely explain why failures occurred or how to resolve them.

This application transforms **'Read logs and guess the cause'** into **'Ask AI and get an evidence-based explanation.'**

## 2. Use Case & Workflow

**Target Users:** Data engineers and on-call engineers on the data platform team.

### Current Troubleshooting Workflow

1. A Spark job fails and triggers an alert.
2. Engineer logs into AWS/GCP console and investigates CloudWatch or Cloud Logging.
3. Engineer examines Spark UI stage details and execution metrics.
4. Engineer identifies potential root causes, such as data skew, out-of-memory errors, or serialization issues.
5. Engineer searches internal documentation or consults colleagues.
6. Engineer implements a fix and reruns the pipeline.

### AI-Powered Workflow

The application automates three major steps:

- **Log Aggregation:** Automatically retrieves relevant execution logs and metrics.
- **Historical Failure Retrieval:** Searches previously resolved incidents for similar failure patterns using vector similarity search.
- **Root Cause Explanation:** Uses Gemini to generate evidence-based explanations and remediation recommendations.

**Example AI-generated explanation:**

> Executor 12 experienced severe shuffle spill on the `customer_id` dimension. Consider enabling AQE skew join handling or broadcasting the dimension table if its size permits.

The response includes a confidence score and references to similar historical incidents.

## 3. AI Features

| Feature | Implementation | Business Value |
|---|---|---|
| Prompt Engineering | Design a grounded system prompt requiring Gemini to use only provided logs and historical cases. Prohibit invented stage numbers, executor IDs, and metrics. | Reduces hallucinations and ensures traceable failure explanations. |
| Structured Outputs | Enforce JSON responses containing `root_cause`, `evidence`, `suggested_fix`, `confidence`, and `similar_cases`. | Enables consistent frontend rendering and downstream automation. |
| RAG + Vector Search | Store historical failure summaries, resolutions, and embeddings in BigQuery. Retrieve top-K similar incidents and inject them into the Gemini prompt. | Reuses historical troubleshooting knowledge to improve explanations. |
| Evaluation Framework | Evaluate retrieval using Hit Rate@3 and generation using root cause accuracy and groundedness. Collect online user feedback. | Measures system quality and guides continuous improvement. |
| Observability | Use OpenTelemetry to trace log retrieval, embedding generation, vector search, Gemini calls, token usage, and end-to-end latency. | Identifies performance bottlenecks and monitors operational cost. |

## 4. Technical Architecture

### Architecture Overview

A single Cloud Run service hosts both the frontend and backend:

- **Frontend:** Lightweight HTML/JavaScript application.
- **Backend:** Python FastAPI application.
- **Deployment:** Containerized application deployed to Cloud Run.

### GCP Service Selection

| Layer | GCP Service | Purpose |
|---|---|---|
| Frontend / Backend | Cloud Run | Hosts the web application and API with serverless autoscaling. |
| LLM | Vertex AI + Gemini | Generates failure explanations using the Google Gen AI SDK. |
| RAG Retrieval | BigQuery Vector Search | Stores and retrieves historical failure cases using semantic similarity. |
| Embedding Generation | BigQuery `AI.GENERATE_EMBEDDING` | Generates vector embeddings directly in BigQuery using `text-embedding-005`. |
| Log / Metric Ingestion | Cloud Logging + Cloud Monitoring API | Retrieves Spark job logs and execution metrics. |
| Observability | OpenTelemetry + Cloud Trace + Cloud Logging + Cloud Monitoring | Traces LLM execution, latency, token usage, and application health. |
| Secret Management | Secret Manager | Securely stores credentials and sensitive configuration. |
| CI/CD | Cloud Build + Artifact Registry | Builds container images and supports automated Cloud Run deployment. |

### End-to-End Data Flow

```text
User submits Spark job ID
          |
          v
Cloud Run Backend (FastAPI)
          |
          v
Retrieve error logs from Cloud Logging
          |
          v
Generate query embedding
          |
          v
BigQuery Vector Search
          |
          v
Retrieve top-K similar historical failures
          |
          v
Construct grounded Gemini prompt
          |
          v
Vertex AI / Gemini
          |
          v
Generate structured JSON explanation
          |
          v
Return response to frontend
```

### Data Preparation

Build an initial RAG knowledge base containing 20–30 simulated Spark failure cases.

Each case includes:

- Original log snippets.
- Failure category and root cause.
- Relevant execution context.
- Human-verified remediation steps.
- Text embedding.

Generate embeddings and store the records in BigQuery for semantic retrieval.

## 5. Prompt Engineering & Structured Outputs

### Sample System Prompt

```text
You are a strictly grounded Spark failure analyst.

Answer ONLY using the provided error logs and historical case context.

Do NOT invent stage numbers, executor IDs, or metrics
that are not present in the context.

If the provided context does not contain enough information
to determine the root cause, explicitly state the uncertainty.

Return valid JSON matching the provided schema.
```

### Sample User Input

```text
Job ID: spark-etl-gold-features-20250612-001

Error:
org.apache.spark.shuffle.FetchFailedException:
Failed to connect to /10.0.12.45:7337

Context:
[2 retrieved historical cases]
[Relevant error log snippets]
```

### Expected Output: Structured JSON

```json
{
  "root_cause": "Executor loss caused shuffle fetch failure, likely triggered by an out-of-memory event.",
  "evidence": "Log shows 'ExecutorLostFailure (executor 7 exited caused by one of the running tasks)' appearing before FetchFailedException.",
  "suggested_fix": [
    "Check executor memory configuration and increase spark.executor.memory if memory pressure is confirmed.",
    "Enable spark.sql.adaptive.enabled to allow AQE to optimize skewed joins.",
    "Investigate whether data skew caused an executor OOM."
  ],
  "confidence": "medium",
  "similar_cases": [
    "case-20250501-003: Similar FetchFailed, resolved by increasing executor memory.",
    "case-20250415-011: Resolved through AQE skew join optimization."
  ]
}
```

### Output Validation Strategy

- **Structured JSON:** Enforce the response schema and validate generated output before returning it to the frontend.
- **Evidence Grounding:** Require specific supporting log lines for factual claims.
- **Confidence Scoring:** Allow the UI to flag low-confidence responses for human review.
- **Historical Traceability:** Include references to retrieved cases so engineers can inspect previous resolutions.

## 6. Evaluation Strategy

### Offline Evaluation

Build a golden evaluation dataset containing 15–20 historically failed jobs.

Each example should include a human-verified root cause category, such as:

- Out-of-memory (OOM).
- Data skew.
- Serialization failure.
- Network connectivity.
- Shuffle fetch failure.

**Evaluation Metrics**

| Metric | Description |
|---|---|
| Retrieval Hit Rate@3 | Percentage of queries where the correct historical failure case appears in the top three retrieved results. |
| Root Cause Accuracy | Percentage of generated explanations matching the human-annotated root cause category. |
| Groundedness | Measures whether factual claims in the generated explanation are supported by the provided logs or historical cases. |

**LLM-as-a-Judge:** Use Gemini to automatically evaluate groundedness and explanation quality, with 20% of results manually reviewed to calibrate evaluation consistency.

### Online Evaluation

After deployment:

- Collect user feedback through helpful / not helpful buttons.
- Track zero-result queries, where no relevant historical failure case is retrieved.
- Monitor low-confidence explanations.
- Use feedback and unresolved incidents to continuously expand the knowledge base.

## 7. Observability & Monitoring

### Instrumentation

Use OpenTelemetry to instrument the Cloud Run application and export telemetry to Google Cloud observability services.

### Per-Request Distributed Tracing

Create one trace per user query, with the following spans:

```text
fetch_logs
    |
    v
generate_embedding
    |
    v
vector_search
    |
    v
gemini_generate
    |
    v
return_response
```

Each span records:

- Execution duration.
- Operation status.
- Relevant error details.
- Token usage where available.

### Monitoring Metrics

| Category | Metrics |
|---|---|
| Latency | p50 / p95 / p99 end-to-end latency and individual stage latency. |
| Cost | Daily Gemini input/output token consumption, grouped by query type. |
| Errors | Log retrieval failure rate, embedding generation failure rate, Gemini API error rate (429/500). |
| Quality Signals | Zero-retrieval-result rate, low-confidence response rate, and negative user feedback rate. |

### Dashboard & Alerts

Build a Cloud Monitoring dashboard with time-series visualizations for the metrics above.

Configure alerts for:

| Alert | Threshold |
|---|---|
| p95 End-to-End Latency | Greater than 10 seconds |
| Application Error Rate | Greater than 5% |
| Zero-Result Retrieval Rate | Greater than 20% |

These thresholds are initial targets and should be calibrated against production traffic and service-level objectives.

## 8. Repository Structure

```text
pipeline-failure-explainer/
├── README.md
├── app/
│   ├── main.py              # FastAPI backend
│   ├── static/
│   │   └── index.html       # Frontend
│   └── requirements.txt
├── data/
│   └── seed_cases.json      # 20–30 simulated failure cases
├── scripts/
│   ├── load_embeddings.py   # BigQuery embedding generation
│   └── create_index.py      # BigQuery vector index creation
├── Dockerfile
├── cloudbuild.yaml
└── .env.example
```

## 9. Getting Started

**Project Status:** Planned implementation.

### Prerequisites

- A Google Cloud Platform project.
- Python 3.10+.
- Google Cloud CLI (`gcloud`).
- Enabled GCP APIs:
  - Vertex AI API.
  - BigQuery API.
  - Cloud Run API.
  - Cloud Logging API.
  - Cloud Monitoring API.
  - Cloud Build API.
  - Artifact Registry API.

### Setup

1. Configure GCP project and authentication.
2. Enable the required APIs.
3. Create a BigQuery dataset.
4. Load historical failure cases into BigQuery.
5. Generate embeddings and create the vector index.
6. Configure the Cloud Run service account and IAM permissions.
7. Configure access to Cloud Logging and Vertex AI.

### Build & Deploy

Build and submit the container image:

```bash
gcloud builds submit
```

Deploy the application to Cloud Run:

```bash
gcloud run deploy pipeline-failure-explainer \\
  --image REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/IMAGE \\
  --region REGION \\
  --platform managed
```

### Test

1. Open the deployed Cloud Run application.
2. Submit a sample Spark job ID.
3. Verify that the application retrieves the relevant logs.
4. Verify that BigQuery returns similar historical failure cases.
5. Validate the Gemini-generated JSON response.
6. Confirm that the frontend displays root cause, evidence, suggested fixes, confidence, and similar cases.

## 10. Future Enhancements

- **Automated Remediation:** Integrate with Cloud Composer to trigger approved recovery workflows.
- **Multi-Agent Troubleshooting:** Introduce specialized agents for log analysis, Spark performance diagnosis, and remediation recommendations.
- **Knowledge Base Expansion:** Automatically ingest resolved production incidents into the RAG knowledge base after human verification.
- **Advanced Retrieval:** Combine vector similarity search with keyword search, metadata filtering, and reranking.
- **Proactive Failure Detection:** Analyze execution metrics and historical patterns to identify potential failures before jobs terminate.

---

**Key Takeaway:** Pipeline Failure Explainer demonstrates how to combine GCP-native services, BigQuery Vector Search, Vertex AI Gemini, and RAG to turn historical pipeline failures into reusable operational knowledge and actionable troubleshooting guidance.
