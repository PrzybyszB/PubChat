import os

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import create_engine, text

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

client = OpenAI(
    api_key=OPENAI_API_KEY
)

engine = create_engine(
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

TABLE_NAME = "pubmed_articles_raw"

QUERY_MAP = {

    "fiber_deficiency": {
        "query": """
        low dietary fiber intake
        gut health
        cardiovascular disease
        metabolic health
        """
    },

    "sodium_excess": {
        "query": """
        excessive sodium intake
        hypertension
        cardiovascular disease
        blood pressure
        """
    }
}

def generate_query_embedding(query_text: str):
    '''Generate query question in embedding'''

    response = client.embeddings.create(model="text-embedding-3-small",input=query_text)

    return response.data[0].embedding

def retrieve_candidates(query_text: str, top_k: int = 20):
    '''Pgvector cosine distance is converted to similarity score'''
    query_embedding = generate_query_embedding(query_text)

    query = text(f"""
        SELECT
            pubmed_id,
            title,
            abstract,
            publication_type,
            quality_score,
            llm_study_subject,
            llm_final_score,

            1 - (
                embedding <=> CAST(:query_embedding AS vector)
            ) AS similarity

        FROM {TABLE_NAME}

        WHERE embedding IS NOT NULL
            AND llm_final_score IS NOT NULL

        ORDER BY embedding <=> CAST(:query_embedding AS vector)

        LIMIT :top_k
    """)

    with engine.connect() as conn:

        result = conn.execute(
            query,{"query_embedding": str(query_embedding),"top_k": top_k})

        return [
            dict(row._mapping)
            for row in result
        ]

def rerank_articles(candidates):

    for article in candidates:

        normalized_quality = (article["llm_final_score"] / 9)

        # Final ranking combines semantic similarity and article quality on the specific weight
        article["retrieval_score"] = (article["similarity"] * 0.7 + normalized_quality * 0.3)

    return sorted(
        candidates,
        key=lambda x: x["retrieval_score"],
        reverse=True
    )

def retrieve_articles(query_text: str, top_k_candidates: int = 20, final_top_k: int = 3):

    candidates = retrieve_candidates(query_text=query_text, top_k=top_k_candidates)

    ranked = rerank_articles(candidates)

    return ranked[:final_top_k]


if __name__ == "__main__":

    results = retrieve_articles(query_text=QUERY_MAP["fiber_deficiency"]["query"])

    for idx, article in enumerate(results, start=1):

        print(f"\n--- RESULT {idx} ---")

        print(f"Title: {article['title']}")

        print(f"Pubmed Id: {article['pubmed_id']}")

        print(f"Similarity: {article['similarity']:.3f}")

        print(f"Final quality score: {article['llm_final_score']}")

        print(f"Final Score: {article['retrieval_score']:.3f}")



        