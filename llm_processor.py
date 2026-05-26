# import os
# import json
# from typing import Optional, List
# from dotenv import load_dotenv
# from openai import OpenAI
# from pydantic import BaseModel
# from sqlalchemy import create_engine, text

# load_dotenv()


# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# POSTGRES_USER = os.getenv("POSTGRES_USER")
# POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
# POSTGRES_DB = os.getenv("POSTGRES_DB")
# POSTGRES_HOST = os.getenv("POSTGRES_HOST")
# POSTGRES_PORT = os.getenv("POSTGRES_PORT")


# client = OpenAI(api_key=OPENAI_API_KEY)

# engine = create_engine(f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

# TABLE_NAME = "pubmed_articles_raw"

# # Pydantic models
# class ArticleForLLM(BaseModel):
#     pubmed_id: str
#     title: str
#     abstract: str

# class ExtractedMetadata(BaseModel):
#     pubmed_id: str
#     llm_is_human: Optional[bool]
#     llm_is_animal: Optional[bool]
#     sample_size: Optional[int]
#     study_population: Optional[bool]
#     confidecnce_note: Optional[bool]


# SYSTEM_PROMPT = """
# You extract structured metadata from scientific abstracts.

# Rules:
# - Use ONLY information explicitly stated in the abstract
# - Do NOT guess
# - If information is missing return null
# - Human study means human participants were studied
# - Animal study means animal models were used
# - Sample size must be explicitly stated
# - Return valid JSON only
# - Do not include markdown
# """


# def fetch_articles(limit: int = 15) -> List[ArticleForLLM]:
#     '''Fetching articles from postgre'''

#     query = text(f"""
#                  SELECT pubmed_id, title, abstract
#                  FROM {TABLE_NAME}
#                  WHERE abstract IS NOT NULL
#                  AND abstract != ''
#                  AND llm_is_human IS NULL
#                  LIMIT :limit """)
    
#     with engine.connect() as conn:
#         result = conn.execute(query, {"limit": limit})

#         articles = []

#         for row in result:
#             articles.append(
#                 ArticleForLLM(
#                     pubmed_id=row.pubmed_id,
#                     title=row.title,
#                     abstract=row.abstract
#                 )
#             )
        
#     return articles


# def create_batches(data: List, batch_size: int):
#     '''Splits the input list into smaller groups with a specified batch size and returns them one by one using a generator (yield)'''

#     for i in range(0,len(data), batch_size):
#         yield data[i:i + batch_size]

# def build_user_prompt(articles: List[ArticleForLLM]) -> str:

#     content = """Extract metadata from the following abstracts. Return JSON array."""

#     for idx, article in enumerate(articles, start=1):
#         content += f"""
# Abstract {idx}

# PMID
# {article.pubmed_id}

# TITLE:
# {article.title}

# ABSTRACT:
# {article.abstract}
# """
        
#     return content


# def extract_metadata_with_llm(articles: List[ArticleForLLM]) -> List[ExtractedMetadata]:
    
#     user_prompt = build_user_prompt(articles)

#     response = client.chat.completions.create(
#         model="gpt-4.1-mini",
#         temperature=0,
#         response_format={"type": "json_object"},
#         messages=[
#             {
#                 "role": "system",
#                 "content": SYSTEM_PROMPT
#             },
#             {
#                 "role": "user",
#                 "content" : user_prompt
#             }
#         ]
#     )

#     raw_content = response.choices[0].message.content

#     parsed_json = json.loads(raw_content)

#     results = []

#     for item in parsed_json["articles"]:

#         results.append(
#             ExtractedMetadata(
#                 pubmed_id=item.get("pubmed_id"),
#                 is_human_study=item.get("is_human_study"),
#                 is_animal_study=item.get("is_animal_study"),
#                 sample_size=item.get("sample_size"),
#                 study_population=item.get("study_population"),
#                 confidence_note=item.get("confidence_note")
#             )
#         )

#     return results



# def update_article_metadata(results: List[ExtractedMetadata]):
#     '''Updating data base'''

#     query = text(f"""
#         UPDATE {TABLE_NAME}
#         SET
#             llm_is_human = :llm_is_human,
#             llm_sample_size = :llm_sample_size,
#             llm_justification = :llm_justification
#         WHERE pubmed_id = :pubmed_id
#     """)

#     with engine.connect() as conn:

#         for item in results:

#             conn.execute(
#                 query,
#                 {
#                     "pubmed_id": item.pubmed_id,
#                     "llm_is_human": item.is_human_study,
#                     "llm_sample_size": item.sample_size,
#                     "llm_justification": item.confidence_note
#                 }
#             )

#         conn.commit()



# def run_pipeline():

#     print(f"Fetching articles from database....")

#     articles = fetch_articles(limit = 15)

#     print(f"Fetched {len(articles)} articles")

#     batches = list(create_batches(articles,batch_size=5))

#     all_results = []

#     for idx, batch in enumerate(batches, start=1):
#         print(f"\nProcessing batch {idx}/{len(batches)}")
#         try:

#             extracted = extract_metadata_with_llm(batch)

#             all_results.extend(extracted)

#             print(f"Batch {idx} processed successfully")

#         except Exception as e:

#             print(f"Error in batch {idx}")
#             print(str(e))

#     print("\nUpdating database...")

#     update_article_metadata(all_results)

#     print("Done.")


# if __name__ == "__main__":
#     run_pipeline()


import os
import json
from typing import Optional, List

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import create_engine, text


# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")


# =========================================================
# OPENAI CLIENT
# =========================================================

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================================================
# POSTGRES CONNECTION
# =========================================================

engine = create_engine(
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


TABLE_NAME = "pubmed_articles_raw"


# =========================================================
# PYDANTIC MODELS
# =========================================================

class ArticleForLLM(BaseModel):
    pubmed_id: str
    title: str
    abstract: str


class ExtractedMetadata(BaseModel):
    pubmed_id: str
    is_human_study: Optional[bool]
    is_animal_study: Optional[bool]
    sample_size: Optional[int]
    study_population: Optional[str]
    confidence_note: Optional[str]


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You extract structured metadata from scientific abstracts.

Rules:
- Use ONLY information explicitly stated in the abstract
- Do NOT guess
- If information is missing return null
- Human study means human participants were studied
- Animal study means animal models were used
- Sample size must be explicitly stated
- Return valid JSON only
- Do not include markdown
"""


# =========================================================
# FETCH ARTICLES FROM POSTGRES
# =========================================================

def fetch_articles(limit: int = 15) -> List[ArticleForLLM]:

    query = text(f"""
        SELECT
            pubmed_id,
            title,
            abstract
        FROM {TABLE_NAME}
        WHERE abstract IS NOT NULL
          AND abstract != ''
          AND llm_is_human IS NULL
        LIMIT :limit
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"limit": limit})

        articles = []

        for row in result:
            articles.append(
                ArticleForLLM(
                    pubmed_id=row.pubmed_id,
                    title=row.title,
                    abstract=row.abstract
                )
            )

    return articles


# =========================================================
# CREATE BATCHES
# =========================================================

def create_batches(data: List, batch_size: int):

    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


# =========================================================
# BUILD USER PROMPT
# =========================================================

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


# =========================================================
# CALL OPENAI
# =========================================================

def extract_metadata_with_llm(
    articles: List[ArticleForLLM]
) -> List[ExtractedMetadata]:

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

    results = []

    for item in parsed_json["articles"]:

        results.append(
            ExtractedMetadata(
                pubmed_id=item.get("pubmed_id"),
                is_human_study=item.get("is_human_study"),
                is_animal_study=item.get("is_animal_study"),
                sample_size=item.get("sample_size"),
                study_population=item.get("study_population"),
                confidence_note=item.get("confidence_note")
            )
        )

    return results


# =========================================================
# UPDATE POSTGRES
# =========================================================

def update_article_metadata(results: List[ExtractedMetadata]):

    query = text(f"""
        UPDATE {TABLE_NAME}
        SET
            llm_is_human = :llm_is_human,
            llm_sample_size = :llm_sample_size,
            llm_justification = :llm_justification
        WHERE pubmed_id = :pubmed_id
    """)

    with engine.connect() as conn:

        for item in results:

            conn.execute(
                query,
                {
                    "pubmed_id": item.pubmed_id,
                    "llm_is_human": item.is_human_study,
                    "llm_sample_size": item.sample_size,
                    "llm_justification": item.confidence_note
                }
            )

        conn.commit()


# =========================================================
# MAIN PIPELINE
# =========================================================

def run_pipeline():

    print("Fetching articles from database...")

    articles = fetch_articles(limit=15)

    print(f"Fetched {len(articles)} articles")

    batches = list(create_batches(articles, batch_size=5))

    all_results = []

    for idx, batch in enumerate(batches, start=1):

        print(f"\nProcessing batch {idx}/{len(batches)}")

        try:

            extracted = extract_metadata_with_llm(batch)

            all_results.extend(extracted)

            print(f"Batch {idx} processed successfully")

        except Exception as e:

            print(f"Error in batch {idx}")
            print(str(e))

    print("\nUpdating database...")

    update_article_metadata(all_results)

    print("Done.")


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":
    run_pipeline()