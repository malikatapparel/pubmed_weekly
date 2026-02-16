# %%
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import json
# %%

# Load your file
df = pd.read_csv('../data/papers.csv')  # Your file with doi,title,abstract

print(f"Processing {len(df)} favorite papers...", )

df = df.dropna(subset=['doi', 'title', 'abstract'])  # Ensure no missing data

# %%
# Extract metadata we need
favorite_texts = []
metadata = []

for i, row in df.iterrows():
    text = f"{row['title']} {row['abstract']}".lower().strip()
    favorite_texts.append(text)
    
    meta = {
        'doi': row['doi'],
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

# %%
