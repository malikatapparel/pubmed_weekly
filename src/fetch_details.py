import requests
import xml.etree.ElementTree as ET


def fetch_paper(pmid, pubmed_api_key=None):
    '''
    Fetch bibliographic details for a given PubMed ID (PMID) using the NCBI E-utilities API.

    This function queries the NCBI Entrez `efetch` endpoint to retrieve metadata about a 
    PubMed article in XML format. It extracts and returns key bibliographic details such 
    as title, abstract, authors, journal name, and publication year.
    '''
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
        "api_key": pubmed_api_key
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    root = ET.fromstring(r.content)

    article = root.find(".//PubmedArticle")

    title = article.findtext(".//ArticleTitle")
    abstract = " ".join(
        [a.text or "" for a in article.findall(".//AbstractText")]
    )

    authors = []
    for author in article.findall(".//Author"):
        lastname = author.findtext("LastName")
        firstname = author.findtext("ForeName")
        if lastname:
            authors.append(f"{firstname or ''} {lastname}".strip())

    journal = article.findtext(".//Journal/Title")
    pubdate = article.findtext(".//PubDate/Year")

    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "journal": journal,
        "pubdate": pubdate
    }