# %%
import requests
import json
import smtplib
from email.mime.text import MIMEText
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from pymed import PubMed
import os

import requests
import xml.etree.ElementTree as ET
# %%



# %%
email_adress = os.environ.get('RECEIVER_EMAIL')

# LOAD YOUR FAVORITE PAPERS (from extract_metadata.py)
print("Loading your 3 favorite papers...")
model = SentenceTransformer('all-MiniLM-L6-v2')
favorite_embeddings = np.load('favorite_embeddings.npy')
print(f"✓ Loaded embeddings: {favorite_embeddings.shape} (your taste profile)")
# %%
# TRACK SEEN PAPERS (no repeats)
try:
    seen_pmids = set(json.load(open('seen_papers.json', 'r')))
    print(f"✓ Loaded {len(seen_pmids)} previously seen papers")
except FileNotFoundError:
    seen_pmids = set()
    print("✓ No seen papers file - first run")
# 

# STEP 2: SEARCH PUBMED (last 30 days = new + missed papers)
print("Searching PubMed for candidates...")
end_date = datetime.now().strftime('%Y/%m/%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y/%m/%d')

# Neuroscience/eating behavior keywords (customize here)
pubmed_query = '"eating behavior" OR "eating behaviour" OR "food cue" OR "food cue reactivity" OR "reinforcement learning" OR "machine learning" OR fMRI OR EEG OR "go/no-go" OR "go nogo" OR gng OR "response inhibition" OR "response training" OR "reward circuit" OR "ventral striatum" OR "nucleus accumbens" OR "reward processing" OR addiction OR "cue reactivity" OR "approach bias"'

params = {
    'db': 'pubmed',
    'term': pubmed_query,
    'mindate': start_date,
    'maxdate': end_date,
    'datetype': 'pdat',
    'retmax': 10,  # Get 100 candidates
    'retmode': 'json'
}

# %%
# GET FULL DETAILS
if pmids: # if list not empty
    # PyMed takes the articles
    candidate_papers = []
    papers = []
    for pmid in pmids:
        try:
            paper_details = fetch_paper(pmid)
            # First append the paper details to the papers list
            papers.append(paper_details)
            # Then create text for embedding (title + abstract)
            text = f"{paper_details['title']} {paper_details['abstract']}".lower()

            candidate_papers.append((pmid, text))
        except Exception as e:
            print(f"Error fetching details for PMID {pmid}: {e}")


# %%
 # %%   
    # STEP 2B: ML RECOMMENDATION ENGINE  
    if candidate_papers:
        print("Running ML similarity matching...")
        candidate_texts = [paper[1] for paper in candidate_papers]
        candidate_embeddings = model.encode(candidate_texts)
        
        # Compare to your favorites (average vector)
        favorite_avg = favorite_embeddings.mean(axis=0).reshape(1, -1)
        similarities = cosine_similarity(favorite_avg, candidate_embeddings).flatten()
        
        # TOP 10 MATCHES
        top_indices = np.argsort(similarities)[-10:][::-1]
        top_papers = [(similarities[i], candidate_papers[i]) for i in top_indices]
        
        print(f"✓ Found top {len(top_papers)} matches to your 3 favorites")
# %%
top_pmids = [paper[1][0] for paper in top_papers] # retrieve PMIDs of top papers
print(f"Top PMIDs: {top_pmids}")
email_body = "YOUR WEEKLY NEUROSCIENCE RECOMMENDATIONS\n\n"
for pmid in top_pmids:
     top_papers_detail = fetch_paper(pmid)
     link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
     paper_body = f"Title: {top_papers_detail['title']}\nAuthors: {', '.join(top_papers_detail['authors'][:3])}\nJournal: {top_papers_detail['journal']}\nLink: {link}\n\n"
     email_body += paper_body
email_body += "Enjoy your reading!\n\n"
# %%
