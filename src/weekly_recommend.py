'''
Project: Weekly Paper Recommendations
Author: Malika Tapparel
Description:
This script fetches weekly paper recommendations based on your favorite papers and a set of keywords. 
'''

# ===============================
# 1. Define keywords and load your favorite papers
# ===============================
# Neuroscience/eating behavior keywords (customize here)
pubmed_query = '"eating behavior" OR "eating behaviour" OR "food cue" OR "food cue reactivity" OR "reinforcement learning" OR "machine learning" OR fMRI OR EEG OR "go/no-go" OR "go nogo" OR gng OR "response inhibition" OR "response training" OR "reward circuit" OR "ventral striatum" OR "nucleus accumbens" OR "reward processing" OR addiction OR "cue reactivity" OR "approach bias"'
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
import fetch_details

import smtplib
from email.message import EmailMessage



# %%
# ===============================
# 1. Load metadata and get paper candidates from keywords
# ===============================
# LOAD YOUR FAVORITE PAPERS (from extract_metadata.py)
print("Loading your favorite papers...")
model = SentenceTransformer('all-MiniLM-L6-v2')
favorite_embeddings = np.load('favorite_embeddings.npy')
print(f"Loaded embeddings: {favorite_embeddings.shape} (your taste profile)")

# %%
# TRACK SEEN PAPERS (no repeats)
try:
    seen_pmids = set(json.load(open('seen_papers.json', 'r')))
    print(f"Loaded {len(seen_pmids)} previously seen papers")
except FileNotFoundError:
    seen_pmids = set()
    print("No seen papers file - first run")
# 

# STEP 2: SEARCH PUBMED (last 30 days = new + missed papers)
print("Searching PubMed for candidates...")
end_date = datetime.now().strftime('%Y/%m/%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y/%m/%d')



# Get 100 candidatews from last 30 days
params_recent = {
    'db': 'pubmed',
    'term': pubmed_query,
    'mindate': start_date,
    'maxdate': end_date,
    'datetype': 'pdat',
    'retmax': 100,  # Get 100 candidates
    'retmode': 'json'
}

recent_pmids = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', params=params_recent).json()['esearchresult']['idlist']

# Get 100 candidates from last year (excluding last month) to catch missed papers
params_year = {
    'db': 'pubmed',
    'term': pubmed_query,
    'mindate': (datetime.now() - timedelta(days=365)).strftime('%Y/%m/%d'),
    'maxdate': (datetime.now() - timedelta(days=31)).strftime('%Y/%m/%d'),  # Exclude last month
    'datetype': 'pdat', 
    'retmax': 100,
    'retmode': 'json'
}
year_pmids = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', params=params_year).json()['esearchresult']['idlist']

pmids = list(set(recent_pmids + year_pmids) - seen_pmids) # this is ~200 candidates paper. 100 from the last year and 100 from the last month, excluding already seen papers.
print(f"Found {len(pmids)} new candidate papers to evaluate")

# %%
# GET FULL DETAILS

if pmids: # if list not empty
    # PyMed takes the articles
    candidate_papers = []
    papers = []
    for pmid in pmids:
        try:
            paper_details = fetch_details.fetch_paper(pmid)
            # First append the paper details to the papers list
            papers.append(paper_details)
            # Then create text for embedding (title + abstract)
            text = f"{paper_details['title']} {paper_details['abstract']}".lower()

            candidate_papers.append((pmid, text))
        except Exception as e:
            print(f"Error fetching details for PMID {pmid}: {e}")

  
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
        
        print(f"Found top {len(top_papers)} matches to your favorite papers")


# Now we have the top papers, we can prepare the email content
top_pmids = [paper[1][0] for paper in top_papers] # retrieve PMIDs of top papers
print(f"Top PMIDs: {top_pmids}")
email_body = "YOUR WEEKLY NEUROSCIENCE RECOMMENDATIONS\n\n"
for pmid in top_pmids:
     top_papers_detail = fetch_details.fetch_paper(pmid)
     link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
     paper_body = f"Title: {top_papers_detail['title']}\nAuthors: {', '.join(top_papers_detail['authors'][:3])}\nJournal: {top_papers_detail['journal']}\nLink: {link}\n\n"
     email_body += paper_body
email_body += "Enjoy your reading!\n\n"

# Save the seen PMIDs for next time read seen_pmids.json
# add all candidates to seen (even if not top, to avoid repeats)
with open('seen_papers.json', 'w') as f:
    json.dump(list(top_pmids), f)
print(f"Updated seen papers list with {len(top_pmids)} new PMIDs")


# 1. Read secrets from GitHub Actions
smtp_user = os.environ["SMTP_USER"]
smtp_pass = os.environ["SMTP_PASS"]
receiver = os.environ["RECEIVER_EMAIL"]

# 2. Create email
msg = EmailMessage()
msg["Subject"] = "Weekly paper recommendations"
msg["From"] = smtp_user
msg["To"] = receiver
msg.set_content(email_body)

# 3. Connect to Outlook SMTP and send
with smtplib.SMTP("smtp-mail.outlook.com", 587, timeout=30) as server:
    server.starttls()              # secure connection
    server.login(smtp_user, smtp_pass)
    server.send_message(msg)

print("Email sent successfully.")
