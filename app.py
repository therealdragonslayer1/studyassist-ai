"""
StudyAssist AI - Main Flask Application
========================================
This is the main entry point for the StudyAssist AI web application.
It handles all the routes and API endpoints.

Run with: python app.py
"""
from dotenv import load_dotenv
load_dotenv()
import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our custom utility modules
from pdf_processor import PDFProcessor
from qa_engine import QAEngine
from summarizer import Summarizer
from tts import TextToSpeech# ─── App Configuration ───────────────────────────────────────────────────────

app = Flask(__name__)

# Secret key for session management (change in production!)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'studyassist-secret-key-change-me')

# Where uploaded PDFs will be stored temporarily
app.config['UPLOAD_FOLDER'] = 'uploads'

# Maximum file size: 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Only allow PDF files
ALLOWED_EXTENSIONS = {'pdf'}

# ─── Initialize Utilities ────────────────────────────────────────────────────

pdf_processor = PDFProcessor()
qa_engine = QAEngine()
summarizer = Summarizer()
tts = TextToSpeech()

# ─── Helper Functions ─────────────────────────────────────────────────────────

def allowed_file(filename):
    """Check if the uploaded file has a .pdf extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Render the home/landing page."""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Render the main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """
    Handle PDF file upload.
    - Validates file type and size
    - Saves file to uploads/ folder
    - Extracts and processes text
    - Creates FAISS vector store
    """
    try:
        # Check if a file was included in the request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        # Check if user selected a file
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Secure the filename to prevent path traversal attacks
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the file
        file.save(filepath)

        # Process the PDF: extract text, chunk it, create embeddings
        result = pdf_processor.process_pdf(filepath)

        if result['success']:
            # Build the FAISS vector store from the processed chunks
            qa_engine.build_vector_store(result['chunks'])
            return jsonify({
                'success': True,
                'filename': filename,
                'page_count': result['page_count'],
                'chunk_count': result['chunk_count'],
                'message': f"Successfully processed {filename} ({result['page_count']} pages)"
            })
        else:
            return jsonify({'error': result['error']}), 500

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    Answer a user question based on the uploaded PDF.
    Uses RAG (Retrieval-Augmented Generation) pipeline.
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return jsonify({'error': 'Please enter a question'}), 400

        # Check if PDF has been processed
        if not qa_engine.is_ready():
            return jsonify({'error': 'Please upload a PDF first'}), 400

        # Get answer from RAG pipeline
        answer = qa_engine.answer_question(question)

        return jsonify({
            'success': True,
            'question': question,
            'answer': answer
        })

    except Exception as e:
        return jsonify({'error': f'Failed to get answer: {str(e)}'}), 500


@app.route('/api/summarize', methods=['POST'])
def summarize_pdf():
    """
    Generate a summary of the uploaded PDF.
    Returns short summary, detailed summary, and key bullet points.
    """
    try:
        # Check if PDF has been processed
        if not pdf_processor.has_text():
            return jsonify({'error': 'Please upload a PDF first'}), 400

        # Get the extracted text
        text = pdf_processor.get_full_text()

        # Generate summaries using free AI API
        summary = summarizer.summarize(text)

        return jsonify({
            'success': True,
            'short_summary': summary['short'],
            'detailed_summary': summary['detailed'],
            'key_points': summary['key_points']
        })

    except Exception as e:
        return jsonify({'error': f'Summarization failed: {str(e)}'}), 500


@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    """
    Generate practice questions from the uploaded PDF.
    Returns short-answer, MCQ, and conceptual questions.
    """
    try:
        # Check if PDF has been processed
        if not pdf_processor.has_text():
            return jsonify({'error': 'Please upload a PDF first'}), 400

        data = request.get_json() or {}
        regenerate = data.get('regenerate', False)

        # Get the extracted text
        text = pdf_processor.get_full_text()

        # Generate questions using free AI API
        questions = summarizer.generate_questions(text, regenerate)

        return jsonify({
            'success': True,
            'short_answer': questions['short_answer'],
            'mcq': questions['mcq'],
            'conceptual': questions['conceptual']
        })

    except Exception as e:
        return jsonify({'error': f'Question generation failed: {str(e)}'}), 500


@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech using IBM Watson TTS.
    Returns an audio file that can be played in the browser.
    """
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        voice = data.get('voice', 'en-US_AllisonV3Voice')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Convert text to speech
        audio_path = tts.synthesize(text, voice)

        if audio_path:
            return send_file(
                audio_path,
                mimetype='audio/mp3',
                as_attachment=False,
                download_name='response.mp3'
            )
        else:
            return jsonify({'error': 'TTS conversion failed'}), 500

    except Exception as e:
        return jsonify({'error': f'TTS failed: {str(e)}'}), 500


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save user settings (model, voice, theme preferences)."""
    try:
        data = request.get_json()
        # In a real app, you'd save these to a database or session
        # For now, we just acknowledge receipt
        return jsonify({'success': True, 'message': 'Settings saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Run the App ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Make sure the uploads folder exists
    os.makedirs('uploads', exist_ok=True)

    print("=" * 50)
    print("  StudyAssist AI is starting...")
    print("  Open: http://localhost:5000")
    print("=" * 50)

    # Run in debug mode for development
    # Set debug=False for production
    app.run(debug=True, host='0.0.0.0', port=5000)
