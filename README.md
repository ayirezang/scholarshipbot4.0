# GlobalEdu Bridge.AN AI Scholarship Assistant Chatbot

An AI-powered scholarship assistant that helps students from Africa and underserved regions discover fully-funded and partial scholarships matched to their academic profile.

# Features

_Smart Matching_ : RAG powered semantic search across 20+ scholarships
_Grade Conversion_ : Supports WASSCE, BECE, A-Levels, KCSE, US GPA, JAMB, percentages, IB, Baccalaureate, Abitur
_Multiple Interfaces_ : Terminal CLI, Streamlit web app, Flask web API
_Vector Search_ : ChromaDB (primary) with NumPy+sklearn fallback
_Application Guidance_ :Personal statement builder, document checklist
_Deploy Ready_ : Config for Render, Gunicorn, Flask

# Quick Start

bash

# Clone

git clone https://github.com/ayirezang/scholarshipbot4.0.git
cd scholarshipbot4.0

# Install

pip install -r requirements.txt

# Run CLI##

python main.py

# Run Streamlit

streamlit run streamlit_app.py

# Run Flask

gunicorn wsgi:app

```

## Interfaces


Interface: CLI Command:python main.py Description: Terminal-based chatbot
Interface: Streamlit Command:streamlit run streamlit_app.py Description: Rich web UI
Interdace: Flask API Command: gunicorn wsgi:app Description: REST API + web chat at `/`

# Grade Systems Supported

WASSCE (WAEC), BECE (Ghana), A-Levels, KCSE (Kenya), US GPA (4.0), JAMB (Nigeria), Percentage (India), French Baccalaureate, IB Diploma, German Abitur.

# RAG Vector Search

The chatbot uses TF-IDF embeddings + cosine similarity search against pre-processed scholarship data. Two backends:

*ChromaDB* (persistent, fast) :`pip install chromadb`
NumpyStore* (fallback, uses scikit-learn)

Build the index:
`bash
python data/vector_store.py --build


Search:
bash
python data/vector_store.py query "engineering scholarships for Africa" re-embed


## Data Pipeline


scholarships_clean.csv  clean_scholarships.py scholarships_deduped.csv chunk_scholarships.py chunks.json  embed_chunks.py  embeddings.json
vector_store.py chroma_db/


# Tech Stack

Python 3.12, Flask, Streamlit, scikit-learn, NumPy, ChromaDB, Gunicorn

# Deployment

The project includes `render.yaml` for Render.com. Set environment variables:

 OPENROUTER_API_KEY (optional  for LLM-enhanced responses)
`OPENROUTER_MODEL (optional)

## License

MIT


live link:https://scholarshipbot4-0-2.onrender.com
```
