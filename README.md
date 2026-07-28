 # GlobalEdu Bridge.AN  AI Scholarship Assistant Chatbot

An AI-powered scholarship assistant that helps students from Africa and underserved regions discover fully-funded and partial scholarships matched to their academic profile.

# Features

*Smart Matching* : RAG powered semantic search across 20+ scholarships
*Grade Conversion* : Supports WASSCE, BECE, A-Levels, KCSE, US GPA, JAMB, percentages, IB, Baccalaureate, Abitur
*Multiple Interfaces* : Terminal CLI, Streamlit web app, Flask web API
*Vector Search* : ChromaDB (primary) with NumPy+sklearn fallback
*Application Guidance* :Personal statement builder, document checklist
*Deploy Ready* : Config for Render, Gunicorn, Flask

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

| Interface | Command | Description |
|-----------|---------|-------------|
| CLI | `python main.py` | Terminal-based chatbot |
| Streamlit | `streamlit run streamlit_app.py` | Rich web UI |
| Flask API | `gunicorn wsgi:app` | REST API + web chat at `/` |

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


scholarships_clean.csv  clean_scholarships.py scholarships_deduped.csv
 chunk_scholarships.py chunks.json  embed_chunks.py  embeddings.json
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