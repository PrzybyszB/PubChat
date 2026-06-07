import os
from dotenv import load_dotenv
from openai import OpenAI
from retriever import retrieve_articles, QUERY_MAP

load_dotenv()

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a public health nutrition analyst.

Your task is to generate an evidence-based report.

Rules:

- Use only information provided in the input.
- Use retrieved articles as evidence.
- Do not invent findings.
- Do not invent statistics.
- Base conclusions on population statistics and article evidence.
- If the population is below recommendation, focus on consequences of insufficient intake.
- If the population is above recommendation, focus on consequences of excessive intake.
- Write in professional language.
- Maximum 300 words.

Structure:

1. Problem Summary
2. Evidence From Literature
3. Public Health Implications
4. Recommendation
"""

def build_context(nutrient_name, mean_value, median_value, p90_value, pct_low, pct_normal, pct_high,articles):

    context = f"""
NUTRIENT:
{nutrient_name}

POPULATION STATISTICS

Mean_value:
{mean_value}

Median intake:
{median_value}

P90 intake:
{p90_value}

Population below recommendation:
{pct_low}%

Population within recommendation:
{pct_normal}%

Population above recommendation:
{pct_high}%
"""

    for idx, article in enumerate(articles, start=1):

        context += f"""

ARTICLE {idx}

PMID:
{article["pubmed_id"]}

TITLE:
{article["title"]}

QUALITY SCORE:
{article["llm_final_score"]}

ABSTRACT:
{article["abstract"]}

"""

    return context
    
def generate_report(nutrient_name, median_value, mean_value, p90_value, pct_low, pct_normal, pct_high, articles):

    context = build_context(nutrient_name=nutrient_name, median_value=median_value, mean_value=mean_value, p90_value=p90_value, pct_low=pct_low, pct_normal=pct_normal, pct_high=pct_high, articles=articles)


    response = client.chat.completions.create(
        model = "gpt-4.1-mini",
        temperature = 0,
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": context
            }
        ]
    )

    report = response.choices[0].message.content

    sources = "\n".join(
        [
            f"- PMID: {article['pubmed_id']}"
            for article in articles
        ]
    )

    return f"""
{report}

Sources:
{sources}
"""
if __name__ == "__main__":

    report = generate_report(
        nutrient_name="Dietary Fiber",

        median_value=14.2,
        p90_value=27.5,

        pct_low=68.4,
        pct_normal=29.3,
        pct_high=2.3,

        query_text=QUERY_MAP["low_fiber"]["query"]
    )

    print(report)