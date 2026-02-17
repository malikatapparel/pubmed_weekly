import requests
import xml.etree.ElementTree as ET



def fetch_papers(pmids, pubmed_api_key=None, chunk_size=100):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    results = {}

    for i in range(0, len(pmids), chunk_size):
        chunk = pmids[i:i+chunk_size]
        params = {"db": "pubmed", "id": ",".join(map(str, chunk)), "retmode": "xml"}
        if pubmed_api_key:
            params["api_key"] = pubmed_api_key

        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()

        root = ET.fromstring(r.content)
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID") or ""
            title = article.findtext(".//ArticleTitle") or ""
            abstract = " ".join([(a.text or "") for a in article.findall(".//AbstractText")]).strip()

            authors = []
            for author in article.findall(".//Author"):
                lastname = author.findtext("LastName")
                firstname = author.findtext("ForeName")
                if lastname:
                    authors.append(f"{firstname or ''} {lastname}".strip())

            journal = article.findtext(".//Journal/Title") or ""
            pubdate = article.findtext(".//PubDate/Year") or ""

            results[pmid] = {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "pubdate": pubdate,
            }

    return results
