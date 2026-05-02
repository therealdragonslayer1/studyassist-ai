"""
Summarizer Utility
===================
Handles PDF summarization and practice question generation
using free AI APIs (Groq preferred, Gemini as fallback).
"""
from dotenv import load_dotenv
load_dotenv()
import os
import json
import re
from typing import Dict, List, Any

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class Summarizer:
    """
    Generates summaries and practice questions from PDF text.
    
    Uses the Groq API (free tier available) for fast inference.
    Falls back to Gemini if Groq is unavailable.
    """

    def __init__(self):
        groq_key = os.getenv('GROQ_API_KEY')

        if GROQ_AVAILABLE and groq_key:
            self.groq_client = Groq(api_key=groq_key)
            self.model = os.getenv('llama-3.3-70b-versatile')

            if not self.model:
                raise ValueError("GROQ_MODEL not set in .env file")
        else:
            self.groq_client = None
            self.model = None

        # Debug logs
        print("Summarizer Groq available:", GROQ_AVAILABLE)
        print("Summarizer API key loaded:", bool(groq_key))
        print("Summarizer model:", self.model)

    def summarize(self, text: str) -> Dict[str, Any]:
        """
        Generate three types of summaries:
        1. Short summary (2-3 sentences)
        2. Detailed summary (paragraph)
        3. Key bullet points
        
        Args:
            text: The full PDF text
            
        Returns:
            Dict with 'short', 'detailed', and 'key_points' keys
        """
        # Truncate very long texts to avoid token limits
        # Keep first 6000 characters which is usually enough for a good summary
        truncated_text = text[:6000] if len(text) > 6000 else text

        prompt = f"""Analyze the following text and provide a comprehensive summary in JSON format.

Text to summarize:
{truncated_text}

Respond with ONLY a valid JSON object (no markdown, no explanation) with these exact keys:
{{
    "short": "2-3 sentence summary of the main topic and key points",
    "detailed": "A detailed paragraph (5-8 sentences) covering the main concepts, arguments, and conclusions",
    "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"]
}}"""

        response_text = self._call_ai(prompt, max_tokens=800)

        # Parse the JSON response
        try:
            # Clean up common issues with JSON responses
            response_text = self._clean_json_response(response_text)
            result = json.loads(response_text)
            return {
                'short': result.get('short', 'Summary not available'),
                'detailed': result.get('detailed', 'Detailed summary not available'),
                'key_points': result.get('key_points', ['Key points not available'])
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, extract what we can
            return self._fallback_summary(response_text, text)

    def generate_questions(self, text: str, regenerate: bool = False) -> Dict[str, List]:
        """
        Generate practice questions from the PDF text.
        
        Generates:
        - 5 short-answer questions
        - 5 multiple choice questions (MCQs)
        - 3 conceptual/analytical questions
        
        Args:
            text: The full PDF text
            regenerate: If True, generate a different set of questions
            
        Returns:
            Dict with 'short_answer', 'mcq', and 'conceptual' keys
        """
        # Truncate for token limits
        truncated_text = text[:5000] if len(text) > 5000 else text

        # Add variation seed when regenerating
        variation = "Generate a DIFFERENT set of questions than before. " if regenerate else ""

        prompt = f"""Based on the following text, generate practice questions for studying.
{variation}
Text:
{truncated_text}

Generate questions STRICTLY based on the content above.
Respond with ONLY a valid JSON object (no markdown, no explanation):
{{
    "short_answer": [
        {{"question": "Question 1?", "hint": "Brief hint about where to look"}},
        {{"question": "Question 2?", "hint": "Brief hint"}},
        {{"question": "Question 3?", "hint": "Brief hint"}},
        {{"question": "Question 4?", "hint": "Brief hint"}},
        {{"question": "Question 5?", "hint": "Brief hint"}}
    ],
    "mcq": [
        {{
            "question": "MCQ Question 1?",
            "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
            "answer": "A"
        }},
        {{
            "question": "MCQ Question 2?",
            "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
            "answer": "B"
        }},
        {{
            "question": "MCQ Question 3?",
            "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
            "answer": "C"
        }},
        {{
            "question": "MCQ Question 4?",
            "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
            "answer": "A"
        }},
        {{
            "question": "MCQ Question 5?",
            "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
            "answer": "D"
        }}
    ],
    "conceptual": [
        {{"question": "Conceptual question 1 requiring deeper analysis?"}},
        {{"question": "Conceptual question 2 requiring deeper analysis?"}},
        {{"question": "Conceptual question 3 requiring deeper analysis?"}}
    ]
}}"""

        response_text = self._call_ai(prompt, max_tokens=1500)

        try:
            response_text = self._clean_json_response(response_text)
            result = json.loads(response_text)
            return {
                'short_answer': result.get('short_answer', []),
                'mcq': result.get('mcq', []),
                'conceptual': result.get('conceptual', [])
            }
        except json.JSONDecodeError:
            return self._fallback_questions()

    def _call_ai(self, prompt: str, max_tokens: int = 800) -> str:
        """
        Call the AI API with a prompt.
        Tries Groq first, then Gemini as fallback.
        """
        # Try Groq
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful educational assistant. Always respond with valid JSON when asked."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Groq API error in summarizer: {e}")

        # Try Gemini
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.3}
                }
                response = requests.post(url, json=payload, timeout=30)
                data = response.json()
                if 'candidates' in data:
                    return data['candidates'][0]['content']['parts'][0]['text'].strip()
                else:
                    return "Gemini API failed: " + str(data)
            except Exception as e:
                print(f"Gemini API error: {e}")

        # No API available
        return '{"error": "No AI API configured"}'

    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks and clean JSON response."""
        # Remove ```json and ``` markers
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        # Find the first { and last } to extract JSON
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            return text[start:end]
        return text.strip()

    def _fallback_summary(self, response_text: str, original_text: str) -> Dict:
        """Create a basic summary if JSON parsing fails."""
        # Use first 200 chars of the original text as a fallback summary
        short = original_text[:200].strip() + "..."
        return {
            'short': short,
            'detailed': response_text[:500] if response_text else "Summarization failed. Please check your API configuration.",
            'key_points': ["Please configure a valid AI API key to generate summaries"]
        }

    def _fallback_questions(self) -> Dict:
        """Return placeholder questions if generation fails."""
        return {
            'short_answer': [
                {"question": "Please configure your GROQ_API_KEY to generate questions", "hint": "Check .env file"},
            ],
            'mcq': [
                {
                    "question": "What is needed to generate questions?",
                    "options": ["A) GROQ_API_KEY", "B) Nothing", "C) Internet only", "D) Premium plan"],
                    "answer": "A"
                }
            ],
            'conceptual': [
                {"question": "Please add your GROQ_API_KEY to the .env file and try again"}
            ]
        }
