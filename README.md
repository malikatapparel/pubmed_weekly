# Weekly PubMed Paper Recommender

## Overview

This repository automatically sends a weekly email with personalized PubMed paper recommendations.

The system:

1. Uses a list of your favorite papers (PMIDs)
2. Extracts metadata and computes semantic embeddings
3. Searches PubMed for new candidate papers based on a provided search strategy
4. Ranks them using embedding similarity
5. Sends the top matches via email
6. Tracks already-sent papers to avoid duplicates

The current setup is tailored to eating behavior, neurocognition, reinforcement learning, and computational modeling, but can be adapted to any research domain.

---

## Repository Structure

```
your-repo/
│
├── data/
│   └── papers.csv                  # Input list of PMIDs from favorite papers
│
├── src/
│   ├── weekly_recommend.py         # Weekly script (runs via GitHub Actions)
│   └── fetch_metadata.py           # Run when updating favorite papers (once at the start + each time you update your list)
│                                   # Fetches metadata + computes embeddings
│
├── favorite_embeddings.npy         # Saved embedding profile
├── seen_pmids.json                # Tracks already-sent papers (initialize as empty list [])
│
└── .github/
    └── workflows/
        └── weekly_digest.yml       # GitHub Actions scheduler
```

---

## First-Time Setup

### 1. Add your favorite papers & search strategy

1. Add PMIDs of your favorite papers in a csv file 

```
data/papers.csv
```
With columns 'pmids', 'title', 'abstract', 'authors', 'journal', 'pubdate'

Add only the pmids from your favorite papers in the column. The script will do the rest.

2. in `weekly_recommend.py` at the very top of the page you can see the current search strategy, customize to fit your field

### 2. Generate embeddings

Run:

```
python src/fetch_metadata.py
```

This script:

- Fetches metadata for your favorite PMIDs
- Replace your papers.csv file with the full details
- Computes embeddings
- Saves them to `favorite_embeddings.npy`

You only need to run this at the start or when adding new favorite papers.

---

### 3. Initialize the seen file

On the very first run, create a file containing:

```
[]
```

Save it as:

```
seen_pmids.json
```

Place it in the repository root. It is automatically updated after each successful weekly email to include already seen papers.

### 3. Create all your GitHub Secrets & enable actions

1. To run GitHub Actions, you need to define the following GitHub Secrets variables.

In your repository:

Settings → Secrets and variables → Actions (see screenshot below)


Add the following secrets:

```
SMTP_USER        # The email adress to send the mails from
SMTP_PASS        # The app password (≠ google account password, see below)
RECEIVER_EMAIL   # The email to send the newsletter to 
PUBMED_API_KEY   # Pubmed API key
```
<img width="1363" height="634" alt="Screenshot 2026-02-17 at 12 47 17" src="https://github.com/user-attachments/assets/50a0484b-a919-4e5f-a2b6-8f9916afc1f2" />

2. Go to Settings → Actions → General and make sure actions are enabled throughout for your workflow

#### Gmail Setup
Create a dummy Google account to avoid security issues. If you are very nice, I might share mine with you to spare you this hassle.
You must:

1. Enable 2-Step Verification in your Google account
2. Generate an App Password for Mail
3. Use that App Password as `SMTP_PASS`, it is a 16-digit password with spaces.

The script uses:

- Server: `smtp.gmail.com`
- Port: `587`
- Encryption: `STARTTLS`

Adjust if you used another server.

### 4. Create a PubMed API key

To avoid rate limiting errors (HTTP 429: Too Many Requests), you must use a PubMed (NCBI) API key.

1. Go to: https://www.ncbi.nlm.nih.gov/account/
2. Sign in or create an account
3. Generate an API key in your account settings

### 4. Custom your automations

The automation runs every Tuesday morning 7.30 UTC. You can adjust the day in `weekly_recommend.py` script, and the time in the workflow.

---
## Additional details
### `weekly_recommend.py` 

`weekly_recommend.py` is the main automation script. It runs via GitHub Actions and performs the full weekly pipeline:

1. Checks if it is Tuesday (Zurich time)  # You can change for another day
2. Loads your favorite paper embeddings  
3. Queries PubMed for new candidate papers  
4. Computes embedding similarity  
5. Selects the top matches  
6. Sends a recommendation email  
7. Updates `seen_papers.json` to avoid duplicates  

### How Recommendations Are Selected

1. PubMed is queried using a domain-specific search string
2. Candidate titles and abstracts are embedded
3. Cosine similarity is computed against your favorite embeddings (all-MiniLM-L6-v2)
4. The top matches are selected
5. A similarity diagnostic is included in the email

Each weekly email includes and how to troubleshoot:

- Selected papers → If they are not relevant, broaden your PubMed query and/or diversify the favorite papers in `data/papers.csv`.
- Number of screened candidates → If this is low (<200), broaden your search strategy (add OR terms, relax filters, increase `retmax`).
- Mean similarity score
- A qualitative similarity rating → If LOW or MODERATE, your query may be too broad or your favorites too narrow/heterogeneous.
- Direct PubMed links

Enjoy your weekly research digest ☕








