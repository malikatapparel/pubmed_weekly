'''
Project: Weekly PubMed Papers Recommender
Author: Malika Tapparel
Description:
This script fetches weekly paper recommendations based on your favorite papers and a set of keywords. 
'''

# ===============================
# 1. Define keywords and load your favorite papers
# ===============================
# Neuroscience/eating behavior keywords (customize here)
pubmed_query = pubmed_query = '''
(
  /* Eating domain */
  "eating behavior"[tiab] OR "eating behaviour"[tiab] OR
  "eating disorder*"[tiab] OR
  anorexia[tiab] OR bulimia[tiab] OR "binge eating"[tiab] OR
  "food intake"[tiab] OR "food consumption"[tiab] OR
  "food cue*"[tiab] OR
  craving*[tiab] OR
  obesity[tiab] OR overweight[tiab] 
)
AND
(
  /* Mechanisms */
  "reinforcement learning"[tiab] OR
  "model-free"[tiab] OR "model-based"[tiab] OR
  "Pavlovian"[tiab] OR
  "sign-tracking"[tiab] OR
  "goal-tracking"[tiab] OR
  "learning bias"[tiab] OR
  "decision making"[tiab] OR
  valuation[tiab] OR
  "approach bias"[tiab] OR
  "inhibitory control"[tiab] OR
  "response inhibition"[tiab] OR
  "go/no-go"[tiab] OR

  /* Neuroimaging */
  fMRI[tiab] OR EEG[tiab] OR ERP[tiab] OR
  "neuroimaging"[tiab] OR
  "brain activation"[tiab] OR
  "neural correlates"[tiab] OR

  /* Machine learning / prediction */
  "machine learning"[tiab] OR
  "predict*"[tiab] OR
  "classification"[tiab] OR
  "decoding"[tiab] OR
  "multivariate"[tiab] OR
  "MVPA"[tiab] OR
  "computational model*"[tiab]
)
NOT
(
  bariatric[tiab] OR
  "gastric bypass"[tiab] OR
  livestock[tiab] OR
  broiler[tiab] OR
  pig[tiab] OR
  rat[tiab] OR
  mice[tiab]
)
'''
import sys
from datetime import datetime, timedelta

# =============================
# Check if today is Tuesday
now = datetime.now()

if now.weekday() != 1:  # Monday=0, Tuesday=1
    print("Not Tuesday. Exiting.")
    sys.exit(0)

smtp_server = "smtp.gmail.com"
smtp_port = 587

# ===============================
# 2. Import packages and retrieve credentials
# ===============================
import requests
import json
import smtplib
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
from email.message import EmailMessage
import fetch_details
import argparse

# For local run: Retrieve credentials from local file
#try:
#    with open('credentials.json', 'r') as f:
#        creds = json.load(f)
#        smtp_user = creds["smtp_user"]
#        smtp_pass = creds["smtp_pass"]
#        receiver = creds["receiver"]
#        pubmed_api_key = creds["pubmed_api_key"]

# For production run: Retrieve credentials from command line arguments (e.g. from GitHub Actions secrets)
parser = argparse.ArgumentParser(description='PubMed Weekly Recommendation System')
parser.add_argument('--smtp_user', required=True, help='SMTP username for sending emails')
parser.add_argument('--smtp_pass', required=True, help='SMTP password for sending emails')
parser.add_argument('--receiver', required=True, help='Email address to receive the recommendations')
parser.add_argument('--pubmed_api_key', required=True, help='API key for accessing PubMed data')
args = parser.parse_args()

smtp_user = args.smtp_user
smtp_pass = args.smtp_pass
receiver = args.receiver
pubmed_api_key = args.pubmed_api_key
# ===============================
# 3. Load metadata and get paper candidates from keywords
# ===============================
# LOAD YOUR FAVORITE PAPERS (from extract_metadata.py)
print("Loading your favorite papers...")
model = SentenceTransformer('all-MiniLM-L6-v2')
favorite_embeddings = np.load('favorite_embeddings.npy')
print(f"Loaded embeddings: {favorite_embeddings.shape} (your taste profile)")

# TRACK SEEN PAPERS, to avoid repeating the same ones every week
try:
    seen_pmids = set(json.load(open('seen_pmids.json', 'r')))
    print(f"Loaded {len(seen_pmids)} previously seen papers")
except FileNotFoundError:
    seen_pmids = set()
    print("No seen papers file - first run")
# 

#  SEARCH PUBMED (last 30 days = new + missed papers)
print("Searching PubMed for candidates...")
today = datetime.now().strftime('%Y/%m/%d')
last_year = (datetime.now().replace(year=datetime.now().year - 1)).strftime('%Y/%m/%d')
last_2month = (datetime.now() - timedelta(days=60)).strftime('%Y/%m/%d') # papers of last 3 months to catch some missed ones

seen_pmids_factor = int(len(seen_pmids)/3)

# Get candidatews from last year
params_year = {
    'db': 'pubmed',
    'term': pubmed_query,
    'mindate': last_year,
    'maxdate': today,
    'datetype': 'pdat',
    'retmax': 400 + 2*seen_pmids_factor,  # Get 400 candidates and account for some seen ones
    'retmode': 'json',
    "api_key": None
}

year_pmids = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', params=params_year).json()['esearchresult']['idlist']

# Get candidatews from last 60 days 
params_recent = {
    'db': 'pubmed',
    'term': pubmed_query,
    'mindate': last_2month,
    'maxdate': today,
    'datetype': 'pdat',
    'retmax': 200 + seen_pmids_factor,  # Get 100 candidates and account for some seen ones
    'retmode': 'json',
    "api_key": None
}

recent_pmids = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', params=params_recent).json()['esearchresult']['idlist']

pmids = list(
    (set(recent_pmids) | set(year_pmids)) - set(seen_pmids)
)
 # this is ~300 papers
print(f"Found {len(pmids)} new candidate papers to evaluate")

# GET FULL DETAILS
if pmids:
    candidate_papers = []
    # 1) Fetch ALL candidate details once (batched)
    papers_by_pmid = fetch_details.fetch_papers(pmids, pubmed_api_key)

    # 2) Build candidate texts from the cached results
    for pmid in pmids:
        paper_details = papers_by_pmid.get(str(pmid)) or papers_by_pmid.get(pmid)
        if not paper_details:
            print(f"Missing details for PMID {pmid} (skipping)")
            continue

        title = paper_details.get("title", "") or ""
        abstract = paper_details.get("abstract", "") or ""
        text = f"{title} {abstract}".lower().strip()

        # skip empty text (rare but happens)
        if not text:
            continue

        candidate_papers.append((pmid, text))
  
    #  ML RECOMMENDATION ENGINE  
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

n_candidates = len(pmids)
n_selected = len(top_pmids)

# Top 10 indices
top_indices = np.argsort(similarities)[-10:][::-1]

# Top 10 similarity values
top_similarities = similarities[top_indices]

# Mean similarity of top 10
mean_top_similarity = float(np.mean(top_similarities))

if mean_top_similarity < 0.30:
    similarity_diagnostic = "LOW"
elif mean_top_similarity < 0.45:
    similarity_diagnostic = "MODERATE"
elif mean_top_similarity < 0.60:
    similarity_diagnostic = "GOOD"
else:
    similarity_diagnostic = "EXCELLENT"

email_body = ""
email_body += "YOUR WEEKLY RECOMMENDATIONS\n"
email_body += "----------------------------------\n\n"

for pmid in top_pmids:
    top_papers_detail = papers_by_pmid.get(str(pmid)) or papers_by_pmid.get(pmid)
    if not top_papers_detail:
        print(f"Missing cached details for top PMID {pmid}, skipping")
        continue
    link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    paper_body = f"Title: {top_papers_detail['title']}\nAuthors: {', '.join(top_papers_detail['authors'][:3])}\nJournal: {top_papers_detail['journal']}\nLink: {link}\n\n"
    email_body += paper_body
email_body += "Enjoy your reading ☕\n\n"
email_body += "- Malika\n\n"
email_body += "Automated weekly recommender\n"
email_body += f"{n_selected} selected papers from {n_candidates} candidates.\n"
email_body += f"Mean similarity of top 10 papers: {mean_top_similarity:.2f} -> {similarity_diagnostic}\n"

# ===============================
# 4. Send email with recommendations
# ===============================

# Send email
msg = EmailMessage()
msg["Subject"] = "☕ Weekly recommendations"
msg["From"] = smtp_user
msg["To"] = receiver
msg.set_content(email_body)

# send first
with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.send_message(msg)
    print(f"Email sent to {receiver} with {n_selected} papers recommended.")

# only if send succeeded, update seen items
seen_pmids.update(top_pmids)
with open('seen_pmids.json', 'w') as f:
    json.dump(sorted(seen_pmids), f)

