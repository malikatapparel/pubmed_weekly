
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
df = pd.read_csv('data/papers.csv')  # Your file with pmids (PubMed IDs)
df.dropna(subset = ['pmid'], inplace=True)  # Remove rows without PMID

# Set up columns as strings
df['title'] = df['title'].astype(str)
df['abstract'] = df['abstract'].astype(str)
df['journal'] = df['journal'].astype(str)
df['pubdate'] = df['pubdate'].astype(str)
df['authors'] = df['authors'].astype(str)

# Check for empty 'title' row and replace with fetched details
for idx, row in df.iterrows():
    if pd.isna(row['title']):
        pmid = row['pmid']
        details = fetch_details.fetch_paper(pmid)
        # Get first 3 authors, handle different cases
        authors_list = details.get('authors', [])
        if isinstance(authors_list, list):
            first_three = authors_list[:3]  # Take first 3
        else:
            first_three = str(authors_list).split(',')[:3]  # Split string if 
        # Join as single string
        authors_str = ', '.join(first_three) if first_three else ''
        
        df.iloc[idx, df.columns.get_loc('title')] = str(details['title'])
        df.iloc[idx, df.columns.get_loc('abstract')] = str(details['abstract'])
        df.iloc[idx, df.columns.get_loc('journal')] = str(details['journal'])
        df.iloc[idx, df.columns.get_loc('pubdate')] = str(details['pubdate'])
        df.iloc[idx, df.columns.get_loc('authors')] = authors_str # Store only the first 3 authors to save space

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


