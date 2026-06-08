import os
import json
from typing import Optional, List
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import create_engine, text


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

client = OpenAI(api_key=OPENAI_API_KEY)

engine = create_engine(f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")


TABLE_NAME = "pubmed_articles_raw"


class ArticleForLLM(BaseModel):
    pubmed_id: str
    title: str
    abstract: str

class ExtractedMetadata(BaseModel):
    pubmed_id: str
    study_subject: Optional[str]
    llm_justification: Optional[str]

SYSTEM_PROMPT = """
You extract metadata from scientific abstracts.

Rules:
- Use only information explicitly stated in the abstract.
- Never guess.
- Return valid JSON only.
- Do not include markdown.
- Do not add fields that are not requested.

Definitions:

study_subject:
- "human" -> the article contains evidence from human participants, either directly or together with animal studies
- "animal" -> the article contains only animal evidence
- "unknown" -> cannot be determined from the abstract.

confidence_note:
- Provide a short justification for the classification.
- Use only information explicitly mentioned in the abstract.
- Maximum 2 sentences.
- If classification is "unknown", explain why the abstract does not provide enough information.

Return exactly:

{
  "metadata": [
    {
      "pubmed_id": "...",
      "study_subject": "human",
       "confidence_note": "The abstract describes a systematic review of previously published studies. No primary human or animal experiment was conducted."
    }
  ]
}
"""


def fetch_articles(limit: int) -> List[ArticleForLLM]:

    # Articles without abstracts are excluded because LLM classification requires textual context
    query = text(f"""
        SELECT
            pubmed_id,
            title,
            abstract
        FROM {TABLE_NAME}
        WHERE abstract IS NOT NULL
          AND abstract != ''
          AND llm_study_subject IS NULL
        ORDER BY pubmed_id
        LIMIT :limit
    """)

    with engine.connect() as conn:

        result = conn.execute(query, {"limit": limit})

        return [ArticleForLLM(pubmed_id=row.pubmed_id, title=row.title, abstract=row.abstract) for row in result]


# def create_batches(data: List, batch_size: int):

#     for i in range(0, len(data), batch_size):
#         yield data[i:i + batch_size]

def build_user_prompt(articles: List[ArticleForLLM]) -> str:

    content = """
Extract metadata from the following abstracts.

Return JSON array.

"""

    for idx, article in enumerate(articles, start=1):

        content += f"""
ABSTRACT {idx}

PMID:
{article.pubmed_id}

TITLE:
{article.title}

ABSTRACT:
{article.abstract}

"""

    return content

def extract_metadata_with_llm(articles: List[ArticleForLLM]) -> List[ExtractedMetadata]:

    user_prompt = build_user_prompt(articles)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    raw_content = response.choices[0].message.content

    parsed_json = json.loads(raw_content)
    
    if "metadata" not in parsed_json:
        raise ValueError(f"Missing 'metadata' key. Response: {raw_content}")

    results = []

    for item in parsed_json["metadata"]:

        results.append(
            ExtractedMetadata(
                pubmed_id=item.get("pubmed_id"),
                study_subject=item.get("study_subject"),
                confidence_note=item.get("confidence_note")
            )
        )

    return results

def update_article_metadata(results: List[ExtractedMetadata]):

    # Human studies are prioritized over animal-only evidence
    POPULATION_SCORE_MAP = {
        "human": 2,
        "animal": 1,
        "unknown": 0
    }
    query = text(f"""
        UPDATE {TABLE_NAME}
        SET
            llm_study_subject = :llm_study_subject,
            llm_justification = :llm_justification,
            llm_population_score = :llm_population_score,
            llm_final_score = quality_score + :llm_population_score 
        WHERE pubmed_id = :pubmed_id
    """)

    with engine.connect() as conn:

        for item in results:

            population_bonus = POPULATION_SCORE_MAP.get(item.study_subject, 0)
            
            conn.execute(
                query,
                {
                    "pubmed_id": item.pubmed_id,
                    "llm_study_subject": item.study_subject,
                    "llm_justification": item.confidence_note,
                    "llm_population_score": population_bonus
                }
            )

        conn.commit()

def get_pipeline_stats():

    query = text(f"""
        SELECT
            COUNT(*) AS total_articles,

            COUNT(*) FILTER (
                WHERE abstract IS NULL
                   OR abstract = ''
            ) AS no_abstract,

            COUNT(*) FILTER (
                WHERE llm_final_score IS NOT NULL
            ) AS processed
        FROM {TABLE_NAME}
    """)

    with engine.connect() as conn:

        row = conn.execute(query).first()

        return dict(row._mapping)

def main():

    print("Starting metadata extraction pipeline...\n")

    batch_size = 20

    processed_count = 0

    while True:

        articles = fetch_articles(limit=batch_size)

        if not articles:

            print(f"\nNo more articles to process.")

            break

        print(f"Fetched {len(articles)} unprocessed articles")

        try:
            extracted = extract_metadata_with_llm(articles)

            print(f"LLM returned {len(extracted)} classifications")

            if len(extracted) != len(articles):

                print("[WARNING] Number of returned records differs from number of input articles.")

            update_article_metadata(extracted)

            processed_count += len(extracted)

            print(f"Batch completed. Total processed: {processed_count}\n")

        except Exception as e:

            print("\nBatch failed.")
            print(str(e))

            break

    print(f"\nPipeline finished. Processed {processed_count} articles.")

    stats = get_pipeline_stats()

    print("\nPipeline statistics")
    print(f"Total articles: {stats['total_articles']}")
    print(f"Processed: {stats['processed']}")
    print(f"Excluded (no abstract): {stats['no_abstract']}")



if __name__ == "__main__":
    main()