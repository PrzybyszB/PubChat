# Public Health Nutrition Decision Support System

## Overview

This project is a Decision Support System designed for Public Health and Nutrition Analysts. The system combines nutritional intake data with scientific evidence retrieved from PubMed to support population-level nutritional assessments.

The application allows analysts to:

* Upload and process structured nutritional datasets.
* Define nutrient-specific intake thresholds.
* Detect nutrient deficiencies and excesses within a population.
* Calculate descriptive statistics.
* Retrieve relevant scientific literature from PubMed.
* Generate evidence-based public health reports using Retrieval-Augmented Generation (RAG).

The system is intended to support analysts in decision-making and does not replace expert judgment.

---

## Project Objectives

The primary objective of this project is to develop a prototype system capable of:

1. Identifying nutrient deficiencies and excesses in a population dataset.
2. Retrieving relevant scientific evidence from PubMed.
3. Ranking scientific articles using a hybrid quality-scoring approach.
4. Generating structured public health reports using Large Language Models (LLMs).

---

## System Architecture

### Offline Knowledge Base Pipeline

The offline pipeline builds the scientific knowledge base used during report generation.

```text
PubMed
  ↓
articles_parser.py
  ↓
llm_processor.py
  ↓
embedding_processor.py
  ↓
PostgreSQL + pgvector
```

### Pipeline Components

#### articles_parser.py

Responsible for:

* Retrieving scientific articles from PubMed.
* Extracting metadata.
* Calculating an initial article quality score based on:

  * Publication type.
  * Publication year.

#### llm_processor.py

Responsible for:

* Extracting additional metadata using GPT models.
* Determining study population type:

  * Human
  * Animal
  * Unknown
* Assigning additional ranking scores.

#### embedding_processor.py

Responsible for:

* Generating OpenAI embeddings.
* Storing vector representations in PostgreSQL using pgvector.

---

## Online Report Generation Workflow

```text
Analyst Input
(Nutrient, Min Intake, Max Intake)
            ↓
Statistics Engine
            ↓
Problem Detection
            ↓
Retriever
(Vector Search + Re-ranking)
            ↓
Report Generator
            ↓
Public Health Report
```

---

## Statistical Analysis

For a selected nutrient, the system calculates:

* Mean intake
* Median intake
* 90th percentile (P90)
* Percentage below recommendation
* Percentage within recommendation range
* Percentage above recommendation

Based on the population distribution, the system identifies the dominant public health issue:

* Deficiency
* Excess

---

## Retrieval-Augmented Generation (RAG)

The system uses Retrieval-Augmented Generation to improve report quality.

### Retrieval Process

1. Query generation
2. Embedding generation
3. Vector similarity search
4. Article quality re-ranking
5. Top article selection

### Re-ranking Formula

Final retrieval score combines:

* Semantic similarity
* Scientific article quality score

This approach prioritizes both relevance and evidence quality.

---

## Generated Report Structure

The generated report contains:

### 1. Problem Summary

Overview of the identified nutritional issue.

### 2. Evidence From Literature

Summary of scientific evidence retrieved from PubMed.

### 3. Public Health Implications

Potential consequences at the population level.

### 4. Recommendation

Suggested actions for public health practitioners.

### Sources

List of PubMed article identifiers used during report generation.

---

## Technology Stack

### Backend

* Python
* FastAPI

### Data Processing

* Pandas
* NumPy

### Database

* PostgreSQL
* pgvector

### LLM & Embeddings

* OpenAI GPT-4.1-mini
* OpenAI text-embedding-3-small

### Data Sources

* NHANES
* PubMed

---

## Project Structure

```text
project/

├── app/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   │
│   └── services/
│       ├── statistics_engine.py
│       ├── retriever.py
│       └── report_generator.py
│
├── pipelines/
│   ├── articles_parser.py
│   ├── llm_processor.py
│   ├── embedding_processor.py
│   └── pipeline.py
│
├── notebooks/
│   └── nhanes_analysis.ipynb
│
├── docs/
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

## Running the Application

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file:

```env
OPENAI_API_KEY

POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
POSTGRES_HOST
POSTGRES_PORT
```

### 3. Build Knowledge Base

Run:

```bash
python pipelines/pipeline.py
```

This will:

1. Download PubMed articles.
2. Extract metadata.
3. Generate embeddings.
4. Store results in PostgreSQL.

### 4. Start API

```bash
uvicorn app.main:app --reload
```

### 5. Open Swagger UI

```text
http://localhost:8000/docs
```
* This version is prepared: fiber and sodium
---

## Limitations

* The system currently supports a predefined set of nutrients.
* Generated reports require expert review.
* Scientific evidence quality depends on available PubMed literature.
* The system is designed as a decision support tool and should not be used as a standalone source of public health recommendations.

---

## Future Work

Potential future extensions include:

* Support for additional nutrients.
* Automatic PubMed query generation.
* Cohort-specific analysis.
* Advanced evidence quality assessment.
* Integration with additional scientific databases.
* Interactive dashboard for public health analysts.

```
```
