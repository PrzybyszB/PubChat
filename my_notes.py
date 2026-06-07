# TODO 

# zobaczyc czy to co pluje sztuczniak ma sens. te dowody naukowe troche pierdoli trzy po trzy
# Query map jaki powinine byc czy ustawiony dla deficcency i excess dla obydwu wartosci czy nie ? 
# usunąć low_fib high_sod, zostawic tylko mediane i p90, notebook ma byc tylko eksploracyjny
# Dodać komenmtarze do funkcjonaności
# uporządkować kod cały i architekture jakos podzielic na foldery  zoabczyc co jest niepotrzebne 

# Pytanie do Ł. W
# Zastanowić się nad rerank_articles czy retrieval score jest dobry 0.7 dla search i 0.3 dla quality score 
# Ile artykułów robic top ? aktualnie jest top3

'''
# Opis kolumn DR1TOT_J https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DR1TOT_J.htm#SEQN

SEQN - id uzytkownika
WTDRD1 - Oznacza ile osób w populacji USA reprezentuje dany respondent. 5.397605346934028e-79  jest ich 1063 i to oznacza ze Day 1 dietary recall not done/incomplete.
WTDRD2 - Oznacza ile osób w populacji USA reprezentuje dany respondent.  5.397605346934028e-79 jest ich 1002 i to oznacza ze Day 2 dietary recall not done/incomplete.
DR1DRSTZ - Okreslenie jak wiarygodne jest ich raportowania z dnia zywienia. Czemu jest 1,2 4,5 ? Gdzie 3 ? 4 oznacza diete oparta na mleku matki więc nalezalloby to usunąć w dalszych analizach.
DR1EXMER - identyfikator osoby przeprowadzającej wywiad 
DRABF - Oznaczenie niemowląt które są na diecie mleka matki
DRDINT - oznakowanie z ilu dni były zebrane dane 1 czy 2
DR1DBIH - liczba dni miedzy dniem spozycia (dietary recall) a wywiadem. Ile dni minelo miedzy dniem którego dotyczy dieta a dniem przeprowadzonego wywiadu. Kolumna istnieje zeby okreslic ryzyko błędu pamięci ? Czyli im wieksza wartosc tym mniej wartosciowe dane 
DR1DAY - oznakowanie w jakim dniu jest wspomniana dieta 1-7 Ndz - Sob
DR1LANG - język, którego uzywali respondenci. Tabela na stronie
DR1MRESP - kto głównie odpowiadał na pytania do ankeitowanego poniewaz czesto były wywiady przeprowadzane w domu gdzie była obecna rodzina, lub np respondent nie był ws tanie odpowiedziec na pytanie (np. niemowlę lub bariera jezykowa).  Oznaczenie 1-3 oznacza raczej najbardziej wiarygodne. Tabela na stronie
DR1HELP - kto pomogał przy odpowiedziach. Najczystszy przypadek danych jest 12- No one poniewaz respondent sam odpowiadał bez pomocy. Tabela na stronie
'''


'''
Co zrobiłem

1. Sprawdzam sanity check danych i je oczyszczam jednoczesnie zapoznając sie z kolumnami ogólnymi czyli od SEQN - DR1HELP. Reszta kolumn jest wyspecjalizowana
2. WTDRD1 widze ze ma wartość przy niektórych  5.397605346934028e-79 co oznacza bliską zeru. Widze tez zaleznosc ze te same jednostki WTDR2D maja missing value
3. Tworze warstwe silver gdzie będę miał wstępnie ustrykturyzowane dane według siebie
4. Tworze docker-compose z postgresql i zapisuje warstwe silver do niego
5. Przechodzę do warstwy gold
6. Następnie zajmuje sie pobieraniem badan z pubmed. Zastanawiam siejak tworzyc prawidłowe zapytania aby publikacje które pobiore były jak najblizsze zywieniu
'''






# KOD KTÓRY MOZE SIE PRZYDAC
'''
import pandas as pd
import json
from Bio import Entrez

# Set the email address to avoid any potential issues with Entrez
Entrez.email = 'your.email@example.com'

# Define lists of authors and topics
authors = ['Bryan Holland', 'Mehmet Oz', 'Anthony Fauci']  # Example authors, adjust as needed
topics = ['RNA', 'cardiovascular']  # Example topics, adjust as needed

# Define date range
date_range = '("2012/03/01"[Date - Create] : "2022/12/31"[Date - Create])'

# Build the query dynamically based on the available authors and topics
queries = []

if authors:
    author_queries = ['{}[Author]'.format(author) for author in authors]
    queries.append('(' + ' OR '.join(author_queries) + ')')

if topics:
    topic_queries = ['{}[Title/Abstract]'.format(topic) for topic in topics]
    queries.append('(' + ' OR '.join(topic_queries) + ')')

full_query = ' AND '.join(queries) + ' AND ' + date_range

# Search PubMed for relevant records
handle = Entrez.esearch(db='pubmed', retmax=11, term=full_query)
record = Entrez.read(handle)
id_list = record['IdList']

# DataFrame to store the extracted data
df = pd.DataFrame(columns=['PMID', 'Title', 'Abstract', 'Authors', 'Journal', 'Keywords', 'URL', 'Affiliations'])

# Fetch information for each record in the id_list
for pmid in id_list:
    handle = Entrez.efetch(db='pubmed', id=pmid, retmode='xml')
    records = Entrez.read(handle)

    # Process each PubMed article in the response
    for record in records['PubmedArticle']:
        # Print the record in a formatted JSON style
        print(json.dumps(record, indent=4, default=str))  # default=str handles types JSON can't serialize like datetime
        title = record['MedlineCitation']['Article']['ArticleTitle']
        abstract = ' '.join(record['MedlineCitation']['Article']['Abstract']['AbstractText']) if 'Abstract' in record['MedlineCitation']['Article'] and 'AbstractText' in record['MedlineCitation']['Article']['Abstract'] else ''
        authors = ', '.join(author.get('LastName', '') + ' ' + author.get('ForeName', '') for author in record['MedlineCitation']['Article']['AuthorList'])
        
        affiliations = []
        for author in record['MedlineCitation']['Article']['AuthorList']:
            if 'AffiliationInfo' in author and author['AffiliationInfo']:
                affiliations.append(author['AffiliationInfo'][0]['Affiliation'])
        affiliations = '; '.join(set(affiliations))

        journal = record['MedlineCitation']['Article']['Journal']['Title']
        keywords = ', '.join(keyword['DescriptorName'] for keyword in record['MedlineCitation']['MeshHeadingList']) if 'MeshHeadingList' in record['MedlineCitation'] else ''
        url = f"https://www.ncbi.nlm.nih.gov/pubmed/{pmid}"

        new_row = pd.DataFrame({
            'PMID': [pmid],
            'Title': [title],
            'Abstract': [abstract],
            'Authors': [authors],
            'Journal': [journal],
            'Keywords': [keywords],
            'URL': [url],
            'Affiliations': [affiliations]
        })

        df = pd.concat([df, new_row], ignore_index=True)

# Save DataFrame to an Excel file
df.to_excel('PubMed_resultsx.xlsx', index=False)


'''


'''
Pretty XML

with open("xml_text_1.xml", "w", encoding="utf-8") as f:
    f.write(xml_data)
import xml.dom.minidom

dom = xml.dom.minidom.parseString(xml_data)

pretty_xml = dom.toprettyxml()

with open("pretty.xml", "w", encoding="utf-8") as f:
    f.write(pretty_xml)

'''


'''
Jupyter notebook flagi 


'''