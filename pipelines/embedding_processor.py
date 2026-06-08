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

def add_vector():
    '''Creating column to keep embedding, text-embedding-3-small return vector of 1536 number length'''

    with engine.connect() as conn:

        conn.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        
        conn.execute(
            text("""
                ALTER TABLE pubmed_articles_raw
                ADD COLUMN IF NOT EXISTS embedding vector(1536)"""))

        conn.commit()

        print("Vector extension verified.")
        print("Embedding column verified.")

def fetch_articles(limit=20):
    '''Generate embeddings only for articles that have not yet been processed'''

    query = text(f"""
            SELECT pubmed_id,
                 title,
                 abstract
            FROM {TABLE_NAME}
            WHERE embedding IS NULL
            ORDER BY pubmed_id
            LIMIT :limit
""")
    
    with engine.connect() as conn:

        result = conn.execute(
            query,
            {"limit": limit}
        )

        return list(result)
    

def build_embedding_text(row):
    '''Embeddings are generated from both title and abstract to maximize semantic retrieval quality'''

    return f"""
Title:
{row.title}

Abstract:
{row.abstract}
"""

def generate_embedding(text_input):
    '''Getting from OpenAI embedded text'''

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text_input
    )

    return response.data[0].embedding


def update_embedding(pubmed_id, embedding):
    '''Update table with embedding data'''

    embedding_str = str(embedding)
    query = text(f"""
                UPDATE {TABLE_NAME}
                SET embedding = :embedding
                WHERE pubmed_id = :pubmed_id
""")
    
    with engine.connect() as conn:

        conn.execute(query, {"pubmed_id": pubmed_id, "embedding": embedding_str})

        conn.commit()


def main():

    print(f"Starting embedding pipeline...")

    add_vector()

    batch_size = 20

    total_processed = 0

    while True:
        rows = fetch_articles(limit=batch_size)

        if not rows:
            print(f"\nNo more articles.")

            break
    
        print(f"\nFetched {len(rows)} articles")    

        for row in rows:
            try:
                text_input = build_embedding_text(row)
                embedding = generate_embedding(text_input)
                
                update_embedding(row.pubmed_id, embedding)
                total_processed += 1

                print(f"Embedded: {row.pubmed_id}")
            
            except Exception as e:
                print(f"Error {row.pubmed_id}")
                print(str(e))

        print(f"Processed so far: {total_processed}")

    print(f"\nFinished. Total Processed: {total_processed}")


if __name__ == "__main__":
    main()