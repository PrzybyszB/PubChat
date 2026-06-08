from fastapi import FastAPI
from app.models import ReportRequest
from app.services.statistics_engine import calculate_statistics, engine
from app.services.retriever import retrieve_articles
from app.services.raport_generator import generate_report
from app.services.retriever import QUERY_MAP

app = FastAPI()

@app.post("/generate-report")
def generate_report_endpoint(request: ReportRequest):

    stats = calculate_statistics(
        nutrient = request.nutrient,
        min_value = request.min_value,
        max_value = request.max_value,
        engine = engine
    )

    # Select retrieval query based on nutrient and detected population problem
    query_key = (f"{request.nutrient}_{stats.problem}")

    query_text = QUERY_MAP[query_key]["query"]

    articles = retrieve_articles(query_text=query_text, final_top_k=3)

    report = generate_report(
        nutrient_name = request.nutrient,

        mean_value=stats.mean_value,
        median_value=stats.median_value,
        p90_value=stats.p90_value,

        pct_low=stats.pct_low,
        pct_normal=stats.pct_normal,
        pct_high=stats.pct_high,

        articles=articles
    )

    return {"statistics": stats.model_dump(),
            "report": report}
