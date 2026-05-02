# 📚 StudyAssist AI

An intelligent study companion that lets you chat with your PDF documents using AI.

## ✨ Features

- **📄 Smart PDF Upload** — Drag & drop PDF processing with FAISS vector indexing
- **💬 AI Chat** — Ask questions, get answers strictly from your PDF (RAG pipeline)
- **📝 Summarization** — Short, detailed, and bullet-point summaries
- **❓ Practice Questions** — Auto-generated MCQs, short-answer & conceptual questions
- **🔊 Text-to-Speech** — IBM Watson TTS integration with browser fallback
- **🌙 Dark Mode** — Full light/dark theme support

---

## 🚀 Quick Start (Ubuntu / Linux)

### Step 1 — Clone / Download the Project

```bash
cd ~/
# Place the studyassist/ folder here
```

### Step 2 — Create Virtual Environment

```bash
cd studyassist
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** First run downloads the embedding model (~90MB). This is a one-time download.

### Step 4 — Configure API Keys

```bash
cp .env.example .env
nano .env   # or use any text editor
```

Fill in your API keys:

```env
GROQ_API_KEY=your_groq_key_here     # Required — get free at console.groq.com
IBM_API_KEY=your_ibm_key_here       # Optional — for TTS
IBM_URL=https://api.us-south...     # Optional — for TTS
```

### Step 5 — Run the App

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🔑 Getting Free API Keys

### Groq API (Required for AI features)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for free (no credit card required)
3. Go to API Keys → Create API Key
4. Copy to `.env` as `GROQ_API_KEY`

**Free tier:** 14,400 requests/day with Llama3 models

### IBM Watson TTS (Optional — for voice)
1. Go to [cloud.ibm.com](https://cloud.ibm.com)
2. Create a free account
3. Search for "Text to Speech" in the catalog
4. Create a Lite (free) instance
5. Go to Manage → Credentials
6. Copy API Key → `IBM_API_KEY`
7. Copy URL → `IBM_URL`

**Free tier:** 10,000 characters/month

---

## 📁 Project Structure

```
studyassist/
├── app.py                  # Flask main application
├── requirements.txt        # Python dependencies
├── .env.example           # Sample environment file
│
├── templates/
│   ├── index.html         # Landing/home page
│   └── dashboard.html     # Main app dashboard
│
├── static/
│   ├── css/
│   │   ├── main.css       # Shared styles
│   │   └── dashboard.css  # Dashboard-specific styles
│   └── js/
│       ├── main.js        # Shared utilities
│       └── dashboard.js   # Dashboard logic
│
├── uploads/               # Temporary PDF storage
│
└── utils/
    ├── pdf_processor.py   # PDF text extraction & chunking
    ├── qa_engine.py       # RAG pipeline (FAISS + LLM)
    ├── summarizer.py      # Summarization & question generation
    └── tts.py             # IBM Watson Text-to-Speech
```

---

## 🏗 Architecture (How It Works)

```
PDF Upload
    ↓
Text Extraction (PyPDF2 / pdfplumber)
    ↓
Text Chunking (LangChain RecursiveTextSplitter)
    ↓
Embedding Generation (HuggingFace sentence-transformers, local)
    ↓
FAISS Vector Store
    ↓
User Question → Similarity Search → Relevant Chunks
    ↓
Groq LLM (llama3-8b-8192) → Answer
    ↓
IBM Watson TTS → Audio (optional)
```

---

## 🛠 Troubleshooting

**Q: "No module named 'faiss'"**
```bash
pip install faiss-cpu
```

**Q: "Embedding model download is slow"**  
The first run downloads `all-MiniLM-L6-v2` (~90MB). Subsequent runs use the cached version.

**Q: "TTS not working"**  
If IBM Watson is not configured, the app automatically falls back to browser TTS (no setup needed).

**Q: "PDF has no text / can't extract"**  
The PDF might be image-based (scanned). Try a text-based PDF. OCR support can be added with `pytesseract`.

**Q: "GROQ_API_KEY not found"**  
Make sure you copied `.env.example` to `.env` and filled in your key.

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| Flask | Web framework |
| LangChain | Document processing & RAG |
| FAISS | Vector similarity search |
| sentence-transformers | Local text embeddings |
| Groq | Fast LLM inference (free tier) |
| PyPDF2 + pdfplumber | PDF text extraction |
| ibm-watson | Text-to-Speech |

---

## 🙏 Credits

Built with:
- [Flask](https://flask.palletsprojects.com/) — Python web framework
- [LangChain](https://langchain.com/) — LLM application framework
- [FAISS](https://faiss.ai/) — Vector search by Meta
- [Groq](https://groq.com/) — Fast AI inference
- [IBM Watson](https://cloud.ibm.com/) — Text to Speech
- [Sentence Transformers](https://sbert.net/) — Text embeddings

---

*StudyAssist AI — Study smarter, not harder* 📚
