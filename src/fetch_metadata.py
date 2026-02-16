
'''
Project: Weekly Paper Recommendations
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
df = pd.read_csv('../data/papers.csv')  # Your file with doi,title,abstract
df.dropna(subset = ['pmid'], inplace=True)  # Remove rows without PMID

# Check for empty 'title' row and replace with fetched details
for idx, row in df.iterrows():
    if pd.isna(row['title']):
        pmid = row['pmid']
        details = fetch_details.fetch_paper(pmid)

        df.at[idx, 'title'] = details['title']
        df.at[idx, 'abstract'] = details['abstract']
        df.at[idx, 'journal'] = details['journal']
        df.at[idx, 'pubdate'] = details['pubdate']
        df.at[idx, 'authors'] = details['authors']

# Update the dataframe with the new details
df.to_csv('../data/papers.csv', index=False)

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

