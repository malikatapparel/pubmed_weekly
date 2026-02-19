
'''
Project: Weekly PubMed Papers Recommender
Author: Malika Tapparel
Description:
This script fetches metadata for papers from PubMed using their PMIDs, 
creates ML embeddings for the papers, and saves the metadata and embeddings for use in weekly recommendations. 
'''
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import fetch_details # Import custom function to fetch paper details from PubMed

#=============================
# 1. Load papers and fetch missing details
#=============================
# Load your file
df = pd.read_csv('data/papers.csv')  # Your file with pmids (PubMed IDs)
df.dropna(subset = ['pmid'], inplace=True)  # Remove rows without PMID

# Set up columns as strings
df['title'] = df['title'].astype(str)
df['abstract'] = df['abstract'].astype(str)
df['journal'] = df['journal'].astype(str)
df['pubdate'] = df['pubdate'].astype(str)
df['authors'] = df['authors'].astype(str)

# 1) PMIDs that need filling (title is missing)
missing_mask = df['title'].isna()
missing_pmids = df.loc[missing_mask, 'pmid'].astype(str).tolist()

if missing_pmids:
    # 2) Batch fetch once
    papers_by_pmid = fetch_details.fetch_papers(
        missing_pmids,
        pubmed_api_key=None,
        chunk_size=100
    )

    # 3) Fill rows
    for idx, row in df.loc[missing_mask].iterrows():
        pmid = str(row['pmid'])
        details = papers_by_pmid.get(pmid)

        if not details:
            print(f"Missing details for PMID {pmid} (skipping)")
            continue

        authors_list = details.get('authors', [])
        if isinstance(authors_list, list):
            first_three = authors_list[:3]
        else:
            first_three = str(authors_list).split(',')[:3]

        df.at[idx, 'title'] = str(details.get('title', ''))
        df.at[idx, 'abstract'] = str(details.get('abstract', ''))
        df.at[idx, 'journal'] = str(details.get('journal', ''))
        df.at[idx, 'pubdate'] = str(details.get('pubdate', ''))
        df.at[idx, 'authors'] = ', '.join(first_three) if first_three else ''
else:
    print("No missing titles found.")

# Update the dataframe with the new details
df.to_csv('data/papers.csv', index=False)

#=============================
# 1. Extract metadata and create embeddings
#=============================
# Extract metadata
favorite_texts = []
metadata = []

for i, row in df.iterrows():
    text = f"{row['title']} {row['abstract']}".lower().strip()
    favorite_texts.append(text)
    
    meta = {
        'pmid': row['pmid'],
        'title': row['title'],
        'abstract': row['abstract']  # Truncate for storage
    }
    metadata.append(meta)
    
    print(f"✓ {i+1}. {row['title'][:60]}...")

# Create ML embeddings (this is your "reference vector")
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(favorite_texts)
print(f"\nCreating embeddings...")

# Save for weekly recommendations
np.save('favorite_embeddings.npy', embeddings)
json.dump(metadata, open('favorite_metadata.json', 'w'), indent=2)

print("SAVED:")
print("- favorite_embeddings.npy (ML vectors)")
print("- favorite_metadata.json (titles for emails)")
print("Ready for weekly recommendations!")


