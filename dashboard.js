/**
 * StudyAssist AI - Dashboard JavaScript
 * =======================================
 * Handles all dashboard interactions:
 * - Panel navigation
 * - PDF upload
 * - Chat / Q&A
 * - Summarization
 * - Question generation
 * - Text-to-Speech
 * - Settings
 */

// ─── Global State ─────────────────────────────────────────────
const state = {
  pdfUploaded: false,
  currentFile: null,
  chatHistory: [],
  currentPanel: 'upload',
  selectedVoice: localStorage.getItem('sa-voice') || 'en-US_AllisonV3Voice',
};

// ─── Panel Navigation ─────────────────────────────────────────

/**
 * Show a specific panel and update the sidebar navigation.
 * @param {string} panelName - 'upload', 'chat', 'summary', 'questions', 'settings'
 */
function showPanel(panelName) {
  // Hide all panels
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));

  // Show selected panel
  const panel = document.getElementById(`panel-${panelName}`);
  if (panel) panel.classList.add('active');

  // Update nav items
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const navItem = document.getElementById(`nav-${panelName}`);
  if (navItem) navItem.classList.add('active');

  // Update header title
  const titles = {
    upload: '📤 Upload PDF',
    chat: '💬 Ask Questions',
    summary: '📝 PDF Summary',
    questions: '❓ Practice Questions',
    settings: '⚙️ Settings',
  };
  const titleEl = document.getElementById('panelTitle');
  if (titleEl) titleEl.textContent = titles[panelName] || panelName;

  // Track current panel
  state.currentPanel = panelName;

  // Close sidebar on mobile
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar')?.classList.remove('open');
  }
}

// ─── PDF Upload ───────────────────────────────────────────────

/**
 * Handle file selection from input element.
 */
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) uploadFile(file);
}

/**
 * Handle drag-over event (show visual feedback).
 */
function handleDragOver(event) {
  event.preventDefault();
  document.getElementById('uploadZone').classList.add('drag-over');
}

/**
 * Handle drag-leave event (remove visual feedback).
 */
function handleDragLeave(event) {
  document.getElementById('uploadZone').classList.remove('drag-over');
}

/**
 * Handle file drop event.
 */
function handleDrop(event) {
  event.preventDefault();
  document.getElementById('uploadZone').classList.remove('drag-over');
  const file = event.dataTransfer.files[0];
  if (file) uploadFile(file);
}

/**
 * Upload and process a PDF file.
 * @param {File} file - The PDF file to upload
 */
async function uploadFile(file) {
  // Validate file type
  if (!file.name.endsWith('.pdf')) {
    showNotification('Please upload a PDF file only!', 'error');
    return;
  }

  // Validate file size (16MB max)
  const maxSize = 16 * 1024 * 1024;
  if (file.size > maxSize) {
    showNotification('File too large! Maximum size is 16MB.', 'error');
    return;
  }

  // Show upload progress
  const progressDiv = document.getElementById('uploadProgress');
  const progressBar = document.getElementById('uploadProgressBar');
  progressDiv.classList.remove('hidden');

  // Animate progress bar (fake animation while uploading)
  let progress = 0;
  const progressInterval = setInterval(() => {
    progress = Math.min(progress + Math.random() * 15, 85);
    progressBar.style.width = `${progress}%`;
  }, 200);

  try {
    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    showNotification('Uploading and processing PDF...', 'info', 5000);

    // Upload to server
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    // Complete progress bar
    clearInterval(progressInterval);
    progressBar.style.width = '100%';

    if (data.success) {
      // Update state
      state.pdfUploaded = true;
      state.currentFile = file.name;

      // Show success card
      const successCard = document.getElementById('uploadSuccess');
      successCard.classList.remove('hidden');
      document.getElementById('successFileName').textContent = file.name;
      document.getElementById('successDetails').textContent =
        `${data.page_count} pages · ${data.chunk_count} chunks indexed`;

      // Update sidebar file info
      document.getElementById('sidebarFileInfo').classList.remove('hidden');
      document.getElementById('sidebarFileName').textContent = file.name;

      // Update header badge
      document.getElementById('fileStatusBadge').classList.remove('hidden');
      document.getElementById('fileStatusText').textContent = file.name;

      // Show PDF preview
      const previewContainer = document.getElementById('pdfPreviewContainer');
      const previewFrame = document.getElementById('pdfPreviewFrame');
      const objectUrl = URL.createObjectURL(file);
      previewFrame.src = objectUrl;
      previewContainer.classList.remove('hidden');

      showNotification(`✅ "${file.name}" processed successfully!`, 'success');
    } else {
      showNotification(data.error || 'Upload failed. Please try again.', 'error');
      progressBar.style.width = '0%';
      progressDiv.classList.add('hidden');
    }

  } catch (error) {
    clearInterval(progressInterval);
    progressDiv.classList.add('hidden');
    showNotification(`Upload error: ${error.message}`, 'error');
    console.error('Upload error:', error);
  }
}


// ─── Chat / Q&A ───────────────────────────────────────────────

/**
 * Handle Enter key in chat input.
 */
function handleChatKeyDown(event) {
  // Send on Enter (but allow Shift+Enter for new line)
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

/**
 * Auto-resize the chat textarea as user types.
 */
function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

/**
 * Send a chat message and get an AI response.
 */
async function sendMessage() {
  const input = document.getElementById('chatInput');
  const question = input.value.trim();

  if (!question) return;

  if (!state.pdfUploaded) {
    showNotification('Please upload a PDF first!', 'error');
    showPanel('upload');
    return;
  }

  // Clear input and reset height
  input.value = '';
  input.style.height = 'auto';

  // Hide welcome message
  const welcome = document.getElementById('chatWelcome');
  if (welcome) welcome.style.display = 'none';

  // Add user message to chat
  addMessage('user', question);

  // Show typing indicator
  const typingId = addTypingIndicator();

  // Disable send button while processing
  document.getElementById('sendBtn').disabled = true;

  try {
    const data = await apiCall('/api/ask', { question });
    
    // Remove typing indicator
    removeTypingIndicator(typingId);

    // Add AI response
    addMessage('assistant', data.answer);

    // Save to history
    state.chatHistory.push({ role: 'user', content: question });
    state.chatHistory.push({ role: 'assistant', content: data.answer });

  } catch (error) {
    removeTypingIndicator(typingId);
    addMessage('assistant', `Sorry, I encountered an error: ${error.message}. Please check your API configuration.`);
    showNotification(error.message, 'error');
  } finally {
    document.getElementById('sendBtn').disabled = false;
  }
}

/**
 * Add a message bubble to the chat.
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - Message text
 */
function addMessage(role, content) {
  const messagesDiv = document.getElementById('chatMessages');
  const avatar = role === 'user' ? '👤' : '🤖';
  const messageId = `msg-${Date.now()}`;

  const messageHtml = `
    <div class="message ${role}" id="${messageId}">
      <div class="message-avatar">${avatar}</div>
      <div>
        <div class="message-content">${escapeHtml(content)}</div>
        ${role === 'assistant' ? `
          <div class="message-actions">
            <button class="btn-icon" onclick="speakMessageText('${messageId}', '${encodeURIComponent(content)}')" title="Listen to this answer">
              🔊
            </button>
            <audio id="audio-${messageId}" style="display:none;"></audio>
          </div>
        ` : ''}
      </div>
    </div>
  `;

  messagesDiv.insertAdjacentHTML('beforeend', messageHtml);

  // Auto-scroll to bottom
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

/**
 * Add a typing indicator animation.
 */
function addTypingIndicator() {
  const id = `typing-${Date.now()}`;
  const messagesDiv = document.getElementById('chatMessages');
  messagesDiv.insertAdjacentHTML('beforeend', `
    <div class="message assistant" id="${id}">
      <div class="message-avatar">🤖</div>
      <div class="message-content" style="padding: 10px 14px;">
        <span style="display:flex;gap:4px;align-items:center;">
          <span style="animation: bounce 1s infinite 0s;display:inline-block;">●</span>
          <span style="animation: bounce 1s infinite 0.2s;display:inline-block;">●</span>
          <span style="animation: bounce 1s infinite 0.4s;display:inline-block;">●</span>
        </span>
      </div>
    </div>
  `);

  // Add bounce animation
  if (!document.getElementById('bounce-style')) {
    const s = document.createElement('style');
    s.id = 'bounce-style';
    s.textContent = '@keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}';
    document.head.appendChild(s);
  }

  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  document.getElementById(id)?.remove();
}

/**
 * Clear all chat messages.
 */
function clearChat() {
  const messagesDiv = document.getElementById('chatMessages');
  messagesDiv.innerHTML = `
    <div class="chat-welcome" id="chatWelcome">
      <div class="welcome-icon">🤖</div>
      <h3>Ready to answer your questions!</h3>
      <p style="font-size: 0.88rem;">Ask me anything about your uploaded PDF.</p>
    </div>
  `;
  state.chatHistory = [];
}


// ─── Summarization ────────────────────────────────────────────

/**
 * Generate PDF summary.
 */
async function generateSummary() {
  if (!state.pdfUploaded) {
    showNotification('Please upload a PDF first!', 'error');
    showPanel('upload');
    return;
  }

  setButtonLoading('summarizeBtn', 'Summarizing...');

  try {
    const data = await apiCall('/api/summarize');

    // Show summary content
    document.getElementById('summaryContent').classList.remove('hidden');
    document.getElementById('summaryEmpty').classList.add('hidden');

    // Fill in summaries
    document.getElementById('shortSummary').textContent = data.short_summary;
    document.getElementById('detailedSummary').textContent = data.detailed_summary;

    // Fill key points
    const keyPointsList = document.getElementById('keyPointsList');
    keyPointsList.innerHTML = '';
    (data.key_points || []).forEach(point => {
      const li = document.createElement('li');
      li.textContent = point;
      keyPointsList.appendChild(li);
    });

    // Show audio buttons
    document.getElementById('shortSummaryAudio').style.display = 'flex';
    document.getElementById('detailedSummaryAudio').style.display = 'flex';

    showNotification('Summary generated successfully!', 'success');

  } catch (error) {
    showNotification(error.message, 'error');
  } finally {
    resetButton('summarizeBtn');
  }
}

/**
 * Clear summary content.
 */
function clearSummary() {
  document.getElementById('summaryContent').classList.add('hidden');
  document.getElementById('summaryEmpty').classList.remove('hidden');
}


// ─── Question Generation ──────────────────────────────────────

/**
 * Generate practice questions from the PDF.
 * @param {boolean} regenerate - True to generate a different set
 */
async function generateQuestions(regenerate = false) {
  if (!state.pdfUploaded) {
    showNotification('Please upload a PDF first!', 'error');
    showPanel('upload');
    return;
  }

  const btnId = regenerate ? 'generateMoreBtn' : 'generateQBtn';
  setButtonLoading(btnId, 'Generating...');

  try {
    const data = await apiCall('/api/generate-questions', { regenerate });

    // Show questions content
    document.getElementById('questionsContent').classList.remove('hidden');
    document.getElementById('questionsEmpty').classList.add('hidden');

    // Render short answer questions
    renderShortAnswerQuestions(data.short_answer || []);

    // Render MCQs
    renderMCQs(data.mcq || []);

    // Render conceptual questions
    renderConceptualQuestions(data.conceptual || []);

    showNotification('Practice questions generated!', 'success');

  } catch (error) {
    showNotification(error.message, 'error');
  } finally {
    resetButton(btnId);
  }
}

function renderShortAnswerQuestions(questions) {
  const container = document.getElementById('shortAnswerQs');
  container.innerHTML = '';
  questions.forEach((q, i) => {
    container.innerHTML += `
      <div class="question-card">
        <div class="question-number">Q${i + 1}</div>
        <div class="question-text">${escapeHtml(q.question || '')}</div>
        ${q.hint ? `<div class="question-hint">💡 Hint: ${escapeHtml(q.hint)}</div>` : ''}
      </div>
    `;
  });
}

function renderMCQs(questions) {
  const container = document.getElementById('mcqQs');
  container.innerHTML = '';
  questions.forEach((q, i) => {
    const optionsHtml = (q.options || []).map((opt, j) => {
      const letter = String.fromCharCode(65 + j); // A, B, C, D
      return `<div class="mcq-option" onclick="checkMCQAnswer(this, '${letter}', '${q.answer || 'A'}')">${escapeHtml(opt)}</div>`;
    }).join('');

    container.innerHTML += `
      <div class="question-card">
        <div class="question-number">MCQ ${i + 1}</div>
        <div class="question-text">${escapeHtml(q.question || '')}</div>
        <div class="mcq-options">${optionsHtml}</div>
      </div>
    `;
  });
}

function renderConceptualQuestions(questions) {
  const container = document.getElementById('conceptualQs');
  container.innerHTML = '';
  questions.forEach((q, i) => {
    container.innerHTML += `
      <div class="question-card">
        <div class="question-number">Conceptual ${i + 1}</div>
        <div class="question-text">${escapeHtml(q.question || '')}</div>
      </div>
    `;
  });
}

/**
 * Check MCQ answer and show visual feedback.
 */
function checkMCQAnswer(element, selectedLetter, correctLetter) {
  // Get all options in this MCQ
  const optionsContainer = element.parentElement;
  const allOptions = optionsContainer.querySelectorAll('.mcq-option');

  // Mark all options as non-interactive
  allOptions.forEach(opt => {
    opt.style.pointerEvents = 'none';
  });

  // Show correct/incorrect
  const selectedIndex = Array.from(allOptions).indexOf(element);
  const correctIndex = correctLetter.charCodeAt(0) - 65; // Convert A->0, B->1, etc.

  if (selectedIndex === correctIndex) {
    element.classList.add('correct');
    showNotification('✅ Correct!', 'success', 2000);
  } else {
    element.classList.add('incorrect');
    allOptions[correctIndex]?.classList.add('correct');
    showNotification('❌ Incorrect. The correct answer is highlighted.', 'error', 3000);
  }
}

/**
 * Clear all questions.
 */
function clearQuestions() {
  document.getElementById('questionsContent').classList.add('hidden');
  document.getElementById('questionsEmpty').classList.remove('hidden');
}


// ─── Text-to-Speech ───────────────────────────────────────────

/**
 * Convert text from a DOM element to speech.
 * @param {string} elementId - ID of element containing text
 * @param {string} audioId - ID of audio element to play in
 */
async function speakText(elementId, audioId) {
  const textEl = document.getElementById(elementId);
  if (!textEl) return;

  const text = textEl.textContent.trim();
  if (!text) return;

  await requestTTS(text, `audio-${audioId}`);
}

/**
 * Convert a chat message to speech.
 * @param {string} messageId - ID of the message div
 * @param {string} encodedText - URL-encoded text to speak
 */
async function speakMessageText(messageId, encodedText) {
  const text = decodeURIComponent(encodedText);
  await requestTTS(text, `audio-${messageId}`);
}

/**
 * Make TTS API request and play audio.
 * @param {string} text - Text to convert
 * @param {string} audioElementId - Audio element to play in
 */
async function requestTTS(text, audioElementId) {
  try {
    const response = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        voice: state.selectedVoice
      })
    });

    if (!response.ok) {
      const err = await response.json();

      // If IBM Watson not configured, use browser TTS as fallback
      if (err.error && err.error.includes('TTS')) {
        useBrowserTTS(text);
        return;
      }
      throw new Error(err.error || 'TTS failed');
    }

    // Get audio blob and play it
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const audioEl = document.getElementById(audioElementId);
    if (audioEl) {
      audioEl.style.display = 'block';
      audioEl.src = url;
      audioEl.play();
    } else {
      // Fallback: create and play audio directly
      const audio = new Audio(url);
      audio.play();
    }

  } catch (error) {
    console.log('IBM TTS unavailable, using browser TTS:', error.message);
    useBrowserTTS(text);
  }
}

/**
 * Browser fallback TTS (no API needed).
 * @param {string} text - Text to speak
 */
function useBrowserTTS(text) {
  if ('speechSynthesis' in window) {
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);

    showNotification('🔊 Using browser TTS (IBM Watson not configured)', 'info', 3000);
  } else {
    showNotification('Text-to-speech is not supported in this browser.', 'error');
  }
}


// ─── Settings ─────────────────────────────────────────────────

/**
 * Save settings to localStorage.
 */
function saveSettings() {
  const voice = document.getElementById('voiceSelect')?.value;
  const theme = document.getElementById('themeSelect')?.value;

  if (voice) {
    state.selectedVoice = voice;
    localStorage.setItem('sa-voice', voice);
  }

  if (theme) applyTheme(theme);

  showNotification('Settings saved!', 'success');
}


// ─── Clear All ────────────────────────────────────────────────

/**
 * Clear all uploaded data (reset the app).
 */
function clearAll() {
  if (!confirm('Clear all data? This will remove the uploaded PDF and all results.')) return;

  state.pdfUploaded = false;
  state.currentFile = null;
  state.chatHistory = [];

  // Reset UI elements
  document.getElementById('uploadSuccess')?.classList.add('hidden');
  document.getElementById('uploadProgress')?.classList.add('hidden');
  document.getElementById('sidebarFileInfo')?.classList.add('hidden');
  document.getElementById('fileStatusBadge')?.classList.add('hidden');
  document.getElementById('pdfPreviewContainer')?.classList.add('hidden');
  document.getElementById('uploadProgressBar').style.width = '0%';

  clearChat();
  clearSummary();
  clearQuestions();

  // Reset file input
  const fileInput = document.getElementById('fileInput');
  if (fileInput) fileInput.value = '';

  showPanel('upload');
  showNotification('All data cleared.', 'info');
}


// ─── Utilities ────────────────────────────────────────────────

/**
 * Escape HTML to prevent XSS.
 * @param {string} text - Text to escape
 */
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}


// ─── Initialize Dashboard ─────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Set active panel
  showPanel('upload');

  // Load saved voice preference
  const savedVoice = localStorage.getItem('sa-voice');
  if (savedVoice) {
    state.selectedVoice = savedVoice;
    const voiceSelect = document.getElementById('voiceSelect');
    if (voiceSelect) voiceSelect.value = savedVoice;
  }

  console.log('📚 StudyAssist AI Dashboard loaded');
});
