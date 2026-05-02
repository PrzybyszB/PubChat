import requests
from Bio import Entrez

# Set the email address to avoid any potential issues with Entrez
Entrez.email = 'bartass97@gmail.com'

def search_pubmed(query, retmax=50):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json"
    }

    res = requests.get(url,params=params)
    data = res.json()

    return data["esearchresult"]["idlist"]

query = '("Dietary Fiber"[MeSH Terms]) AND ("2020/01/01"[Date - Publication] : "3000"[Date - Publication])'

ids = search_pubmed(query)

print(ids)
