(function() {
  const originalLog = console.log.bind(console);
  console.log = (...args) => {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');
    originalLog(
      `[${hh}:${mm}:${ss}.${ms}]`,
      ...args
    );
  };
})();

// DOM Elements
const statusText = document.getElementById("statusText");
const statusIndicator = document.getElementById("statusIndicator");
const transcriptionArea = document.getElementById("transcriptionArea");
const emptyState = document.getElementById("emptyState");
const languageSelect = document.getElementById("languageSelect");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const clearBtn = document.getElementById("clearBtn");
const copyBtn = document.getElementById("copyBtn");
const exportTxtBtn = document.getElementById("exportTxtBtn");
const exportJsonBtn = document.getElementById("exportJsonBtn");

// Audio and connection state
let socket = null;
let audioContext = null;
let mediaStream = null;
let micWorkletNode = null;

// Transcription state
let transcriptionHistory = [];
let currentPartialTranscription = null;
let isRecording = false;
let currentLanguage = 'en';
let sessionStartTime = null;

// Audio processing constants
const BATCH_SAMPLES = 2048;
const HEADER_BYTES = 8;
const FRAME_BYTES = BATCH_SAMPLES * 2;
const MESSAGE_BYTES = HEADER_BYTES + FRAME_BYTES;

const bufferPool = [];
let batchBuffer = null;
let batchView = null;
let batchInt16 = null;
let batchOffset = 0;

// Initialize batch processing
function initBatch() {
  if (!batchBuffer) {
    batchBuffer = bufferPool.pop() || new ArrayBuffer(MESSAGE_BYTES);
    batchView = new DataView(batchBuffer);
    batchInt16 = new Int16Array(batchBuffer, HEADER_BYTES);
    batchOffset = 0;
  }
}

function flushBatch() {
  const ts = Date.now() & 0xFFFFFFFF;
  batchView.setUint32(0, ts, false);
  batchView.setUint32(4, 0, false); // No TTS flags needed

  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(batchBuffer);
  }

  bufferPool.push(batchBuffer);
  batchBuffer = null;
}

function flushRemainder() {
  if (batchOffset > 0) {
    for (let i = batchOffset; i < BATCH_SAMPLES; i++) {
      batchInt16[i] = 0;
    }
    flushBatch();
  }
}

// Audio context initialization
function initAudioContext() {
  if (!audioContext) {
    audioContext = new AudioContext();
  }
}

// Start microphone capture for transcription
async function startMicrophoneCapture() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: { ideal: 24000 },
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
      }
    });
    
    mediaStream = stream;
    initAudioContext();
    
    await audioContext.audioWorklet.addModule('/static/pcmWorkletProcessor.js');
    micWorkletNode = new AudioWorkletNode(audioContext, 'pcm-worklet-processor');

    micWorkletNode.port.onmessage = ({ data }) => {
      const incoming = new Int16Array(data);
      let read = 0;
      
      while (read < incoming.length) {
        initBatch();
        const toCopy = Math.min(
          incoming.length - read,
          BATCH_SAMPLES - batchOffset
        );
        batchInt16.set(
          incoming.subarray(read, read + toCopy),
          batchOffset
        );
        batchOffset += toCopy;
        read += toCopy;
        
        if (batchOffset === BATCH_SAMPLES) {
          flushBatch();
        }
      }
    };

    const source = audioContext.createMediaStreamSource(stream);
    source.connect(micWorkletNode);
    
    updateStatus('Recording...', true);
    console.log('Microphone capture started');
    
  } catch (err) {
    updateStatus('Microphone access denied', false);
    console.error('Microphone access error:', err);
  }
}

// Clean up audio resources
function cleanupAudio() {
  if (micWorkletNode) {
    micWorkletNode.disconnect();
    micWorkletNode = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (mediaStream) {
    mediaStream.getAudioTracks().forEach(track => track.stop());
    mediaStream = null;
  }
}

// Update UI status
function updateStatus(text, recording = false) {
  statusText.textContent = text;
  if (recording) {
    statusIndicator.classList.add('recording');
  } else {
    statusIndicator.classList.remove('recording');
  }
}

// Create timestamp string
function formatTimestamp(date = new Date()) {
  return date.toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
}

// Create transcription entry element
function createTranscriptionEntry(text, timestamp, isPartial = false, language = 'en') {
  const entry = document.createElement('div');
  entry.className = `transcription-entry ${isPartial ? 'partial' : 'final'}`;
  
  const timestampDiv = document.createElement('div');
  timestampDiv.className = 'transcription-timestamp';
  timestampDiv.innerHTML = `
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
      <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg>
    ${timestamp}
    ${language !== 'en' ? `• ${language.toUpperCase()}` : ''}
    ${isPartial ? '• Listening...' : ''}
  `;
  
  const textDiv = document.createElement('div');
  textDiv.className = 'transcription-text';
  textDiv.textContent = text;
  
  entry.appendChild(timestampDiv);
  entry.appendChild(textDiv);
  
  return entry;
}

// Render transcription area
function renderTranscriptions() {
  // Clear existing content
  transcriptionArea.innerHTML = '';
  
  if (transcriptionHistory.length === 0 && !currentPartialTranscription) {
    transcriptionArea.appendChild(emptyState);
    return;
  }
  
  // Render final transcriptions
  transcriptionHistory.forEach(entry => {
    const element = createTranscriptionEntry(
      entry.text, 
      entry.timestamp, 
      false, 
      entry.language
    );
    transcriptionArea.appendChild(element);
  });
  
  // Render current partial transcription
  if (currentPartialTranscription && currentPartialTranscription.text.trim()) {
    const element = createTranscriptionEntry(
      currentPartialTranscription.text,
      currentPartialTranscription.timestamp,
      true,
      currentPartialTranscription.language
    );
    transcriptionArea.appendChild(element);
  }
  
  // Auto-scroll to bottom
  transcriptionArea.scrollTop = transcriptionArea.scrollHeight;
}

// Handle incoming transcription messages
function handleTranscriptionMessage({ type, content, language = 'en' }) {
  const timestamp = formatTimestamp();
  
  if (type === "partial_transcription" || type === "partial_user_request") {
    if (content && content.trim()) {
      currentPartialTranscription = {
        text: content.trim(),
        timestamp: timestamp,
        language: language
      };
    } else {
      currentPartialTranscription = null;
    }
    renderTranscriptions();
    return;
  }
  
  if (type === "final_transcription" || type === "final_user_request") {
    // Add partial to history if it exists
    if (currentPartialTranscription) {
      transcriptionHistory.push({
        text: currentPartialTranscription.text,
        timestamp: currentPartialTranscription.timestamp,
        language: currentPartialTranscription.language,
        type: 'final'
      });
      currentPartialTranscription = null;
    }
    
    // Add final transcription if it has content and is different from the last entry
    if (content && content.trim()) {
      const lastEntry = transcriptionHistory[transcriptionHistory.length - 1];
      if (!lastEntry || lastEntry.text !== content.trim()) {
        transcriptionHistory.push({
          text: content.trim(),
          timestamp: timestamp,
          language: language,
          type: 'final'
        });
      }
    }
    
    renderTranscriptions();
    return;
  }
}

// HTML escape function
function escapeHtml(str) {
  return (str ?? '')
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Export functions
function exportAsText() {
  const text = transcriptionHistory
    .map(entry => `[${entry.timestamp}] ${entry.text}`)
    .join('\n');
  
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `transcription_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportAsJson() {
  const data = {
    session: {
      startTime: sessionStartTime,
      endTime: new Date().toISOString(),
      language: currentLanguage
    },
    transcriptions: transcriptionHistory
  };
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `transcription_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function copyToClipboard() {
  const text = transcriptionHistory
    .map(entry => `[${entry.timestamp}] ${entry.text}`)
    .join('\n');
  
  navigator.clipboard.writeText(text)
    .then(() => {
      // Show temporary success feedback
      const originalText = copyBtn.innerHTML;
      copyBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Copied!
      `;
      setTimeout(() => {
        copyBtn.innerHTML = originalText;
      }, 2000);
      console.log("Transcription copied to clipboard");
    })
    .catch(err => {
      console.error("Copy failed:", err);
      updateStatus('Copy failed', false);
    });
}

// Event handlers
startBtn.onclick = async () => {
  if (isRecording) {
    updateStatus("Already recording", true);
    return;
  }
  
  updateStatus("Connecting...", false);
  sessionStartTime = new Date().toISOString();
  
  const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  socket = new WebSocket(`${wsProto}//${location.host}/ws`);
  
  socket.onopen = async () => {
    console.log('WebSocket connected');
    
    // Send language preference
    socket.send(JSON.stringify({
      type: 'set_language',
      language: currentLanguage
    }));
    
    await startMicrophoneCapture();
    isRecording = true;
    
    startBtn.disabled = true;
    stopBtn.disabled = false;
    languageSelect.disabled = true;
  };
  
  socket.onmessage = (evt) => {
    if (typeof evt.data === "string") {
      try {
        const msg = JSON.parse(evt.data);
        handleTranscriptionMessage(msg);
      } catch (e) {
        console.error("Error parsing message:", e);
      }
    }
  };
  
  socket.onclose = () => {
    updateStatus("Connection closed", false);
    flushRemainder();
    cleanupAudio();
    isRecording = false;
    
    startBtn.disabled = false;
    stopBtn.disabled = true;
    languageSelect.disabled = false;
  };
  
  socket.onerror = (err) => {
    updateStatus("Connection error", false);
    cleanupAudio();
    isRecording = false;
    console.error('WebSocket error:', err);
    
    startBtn.disabled = false;
    stopBtn.disabled = true;
    languageSelect.disabled = false;
  };
};

stopBtn.onclick = () => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    flushRemainder();
    socket.close();
  }
  cleanupAudio();
  updateStatus("Stopped", false);
  isRecording = false;
  
  startBtn.disabled = false;
  stopBtn.disabled = true;
  languageSelect.disabled = false;
};

clearBtn.onclick = () => {
  transcriptionHistory = [];
  currentPartialTranscription = null;
  renderTranscriptions();
  
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'clear_history' }));
  }
  
  console.log("Transcription history cleared");
};

// Language selection handler
languageSelect.onchange = () => {
  currentLanguage = languageSelect.value;
  
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      type: 'set_language',
      language: currentLanguage
    }));
  }
  
  console.log("Language changed to:", currentLanguage);
};

// Export button handlers
exportTxtBtn.onclick = exportAsText;
exportJsonBtn.onclick = exportAsJson;
copyBtn.onclick = copyToClipboard;

// Initialize the app
updateStatus("Ready to start", false);
renderTranscriptions();

console.log("Live Transcription app initialized");