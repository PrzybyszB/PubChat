import requests
import os
from Bio import Entrez
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MAIL = os.getenv("MAIL")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# Set the email address to avoid any potential issues with Entrez
Entrez.email = MAIL

# Postgres Config
engine = create_engine(f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

TABLE_NAME = "pubmed_articles_raw"

query = '("Dietary Fiber"[MeSH Terms]) AND ("2020/01/01"[Date - Publication] : "3000"[Date - Publication])'


def search_pubmed(query, retmax=20):
    '''Search PubMed and return list of PubMed IDs'''

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json"
    }

    res = requests.get(url,params=params)
    data = res.json()

    ids = data["esearchresult"]["idlist"]

    # Removing duplicates
    ids = list(dict.fromkeys(ids))

    return ids

ids = search_pubmed(query)

def fetch_details(ids):
    """Fetch article details from PubMed in XML format"""

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    params = {
        "db": "pubmed",
        "id" : ",".join(ids),
        "retmode": "xml"

    }

    res = requests.get(url,params=params)

    return res.text

xml_data = fetch_details(ids)

def parse_articles(xml_data):
    """Parse PubMed XML and extract article metadata"""

    root = ET.fromstring(xml_data)

    articles = []


    # Determination scroing for publication_type
    SCORE_MAP = {
        "Meta-Analysis": 5,
        "Systematic Review": 4,
        "Randomized Controlled Trial": 4,
        "Review": 3,
        "Journal Article": 1
    }

    CURRENT_YEAR = datetime.now().year

    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = article.findtext(".//PMID")
            title = article.findtext(".//ArticleTitle")

             # Multiple publication types possible
            publication_types = [
                p.text
                for p in article.findall(".//PublicationType")
                if p.text
            ]

            # Looking for the highest tag, because its can be multiple publication-types
            points_list = [SCORE_MAP.get(pt, 1) for pt in publication_types]
            
            type_score = max(points_list, default=1)

            year_str = article.findtext(".//PubDate/Year")
            year = int(year_str) if year_str else None


            # Bonus points for publication yaer
            year_bonus = 0
            if year:
                age = CURRENT_YEAR - year
                if age <= 4:
                    year_bonus = 2
                elif age <= 7:
                    year_bonus = 1
                else:
                    year_bonus = 0
            
            total_quality_score = type_score + year_bonus


            abstract = ""
            abstract_nodes = article.findall(".//AbstractText")

            if abstract_nodes:
                abstract = " ".join([a.text for a in abstract_nodes if a.text])

            year = article.findtext(".//PubDate/Year")

            articles.append({
                "pubmed_id": pmid,
                "title": title,
                "publication_type": ", ".join(publication_types),
                "abstract": abstract,
                "year": int(year) if year else None,
                "quality_score": total_quality_score

            })
        except Exception:
            continue

    return articles


parsed_article = parse_articles(xml_data)

def create_table():

    with engine.connect() as conn:

        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                pubmed_id TEXT PRIMARY KEY,
                title TEXT,
                publication_type TEXT,
                abstract TEXT,
                year INTEGER,
                quality_score INTEGER,

                llm_is_human BOOLEAN,
                llm_sample_size INTEGER,
                llm_final_score REAL,
                llm_justification TEXT
            )
        """))

        conn.commit()

create_table()

def save_to_db(parsed_articles):

    inserted_count = 0

    with engine.connect() as conn:

        for article in parsed_articles:

            result = conn.execute(text(f"""
                INSERT INTO {TABLE_NAME} (
                    pubmed_id,
                    title,
                    publication_type,
                    abstract,
                    year,
                    quality_score
                )
                VALUES (
                    :pubmed_id,
                    :title,
                    :publication_type,
                    :abstract,
                    :year,
                    :quality_score
                )
                ON CONFLICT (pubmed_id) DO NOTHING
            """), article)

            if result.rowcount > 0:
                inserted_count += 1

        conn.commit()

    return {
        "inserted": inserted_count,
        "total_articles": len(parsed_articles),
        "duplicates": len(parsed_articles) - inserted_count
    }


result = save_to_db(parsed_article)
print(result)



'''
Quality score 
year, 
journal, 
study_type, <PublicationType> </PublicationType>
population, 
human vs animal_study


'''