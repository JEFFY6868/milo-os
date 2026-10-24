// Milo AI Live Call Web & PWA Client (v2.1)
// Clean Audio Pipeline: Live Audio Visualizer, Dual-Engine STT (SpeechRecognition + Server Gemini MediaRecorder),
// Mobile Audio Autoplay Unlocker, Hardware Mic Mute, and Push-To-Talk.

let callSocket = null;
let callTimerInterval = null;
let callSeconds = 0;
let isCallActive = false;
let isMuted = false;
let isSpeakerMuted = false;
let isMiloSpeaking = false;

// Audio Pipeline & Web Audio Nodes
let audioContext = null;
let analyser = null;
let micStream = null;
let visualizerAnimationId = null;

// Speech Recognition & Fallback Recorder
let speechRecognizer = null;
let speechRecFailCount = 0;
let mediaRecorder = null;
let recordedAudioChunks = [];
let isManualRecording = false;
let vadSilenceTimeout = null;
let isVadRecording = false;
let isTouchActive = false;

// Initialize Lucide Icons, PWA, and Signaling
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  // Register PWA Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('PWA ServiceWorker registration failed:', err);
    });
  }

  // Detect Insecure Context (HTTP over Tailscale IP)
  if (!window.isSecureContext && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    const banner = document.getElementById('insecureBanner');
    if (banner) banner.classList.remove('hidden');
  }

  // Setup Push-To-Talk / Manual Speaking Button
  setupPushToTalkHandlers();

  // Connect to Signaling WebSocket
  connectCallWebSocket();

  // Handle URL params (e.g. ?autocall=1)
  const params = new URLSearchParams(window.location.search);
  if (params.get('autocall') === '1') {
    setTimeout(() => startOutboundCall(), 500);
  }
});

// =========================================================================
// WEBSOCKET SIGNALING (Real-time incoming call push)
// =========================================================================
function connectCallWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/call`;

  try {
    callSocket = new WebSocket(wsUrl);

    callSocket.onopen = () => {
      console.log('✔ Milo Call Signaling connected.');
      updateStatusBadge(true);
    };

    callSocket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleSignalMessage(msg);
      } catch (e) {
        console.error('Signal parse error:', e);
      }
    };

    callSocket.onclose = () => {
      updateStatusBadge(false);
      setTimeout(connectCallWebSocket, 3000);
    };

    callSocket.onerror = (err) => {
      console.warn('Signaling socket error:', err);
    };
  } catch (e) {
    console.error('WebSocket connection failed:', e);
  }
}

function updateStatusBadge(connected) {
  const badge = document.getElementById('systemStatusLabel');
  if (badge) {
    if (connected) {
      badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Ready • Live Audio`;
      badge.className = 'text-[11px] font-mono text-emerald-400 flex items-center gap-1';
    } else {
      badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Reconnecting...`;
      badge.className = 'text-[11px] font-mono text-amber-400 flex items-center gap-1';
    }
  }
}

function handleSignalMessage(msg) {
  if (msg.type === 'incoming_call') {
    triggerIncomingCallUI(msg);
  } else if (msg.type === 'call_ended') {
    endActiveCall(false);
  }
}

// =========================================================================
// INCOMING CALL HANDLING
// =========================================================================
function triggerIncomingCallUI(callData = {}) {
  if (isCallActive) return;

  const screenStandby = document.getElementById('screenStandby');
  const screenIncoming = document.getElementById('screenIncoming');
  const screenActive = document.getElementById('screenActive');
  const subtext = document.getElementById('incomingCallSubtext');

  if (callData.text && subtext) {
    subtext.textContent = callData.text.length > 50 ? callData.text.substring(0, 50) + '...' : callData.text;
  }

  screenStandby.classList.add('hidden');
  screenActive.classList.add('hidden');
  screenIncoming.classList.remove('hidden');

  const ringtone = document.getElementById('ringtoneAudio');
  if (ringtone) {
    ringtone.currentTime = 0;
    ringtone.play().catch((err) => {
      console.log('Ringtone auto-play requires user interaction:', err);
    });
  }

  if ('vibrate' in navigator) {
    try { navigator.vibrate([400, 200, 400, 200, 800]); } catch (e) {}
  }
}

function simulateIncomingCall() {
  triggerIncomingCallUI({
    caller: 'Milo AI',
    text: 'Screenplay Brainstorming Session'
  });
}

function declineCall() {
  stopRingtone();
  if (callSocket && callSocket.readyState === WebSocket.OPEN) {
    callSocket.send(JSON.stringify({ type: 'call_declined' }));
  }
  showScreen('standby');
}

function stopRingtone() {
  const ringtone = document.getElementById('ringtoneAudio');
  if (ringtone) {
    ringtone.pause();
    ringtone.currentTime = 0;
  }
  if ('vibrate' in navigator) {
    try { navigator.vibrate(0); } catch (e) {}
  }
}

// Unlock Mobile Audio Autoplay Policy on first tap gesture
function unlockMobileAudio() {
  const speaker = document.getElementById('miloSpeakerAudio');
  if (speaker) {
    speaker.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
    speaker.play().then(() => {
      speaker.pause();
      speaker.currentTime = 0;
    }).catch(() => {});
  }

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!audioContext && AudioCtx) {
    audioContext = new AudioCtx();
  }
  if (audioContext && audioContext.state === 'suspended') {
    audioContext.resume().catch(() => {});
  }
}

// =========================================================================
// ACTIVE CALL & AUDIO PIPELINE
// =========================================================================
async function acceptCall() {
  unlockMobileAudio();
  stopRingtone();
  if (callSocket && callSocket.readyState === WebSocket.OPEN) {
    callSocket.send(JSON.stringify({ type: 'call_accepted' }));
  }
  await initializeCallSession();
}

async function startOutboundCall() {
  unlockMobileAudio();
  showScreen('active');
  await initializeCallSession(true);
}

async function initializeCallSession(isOutbound = false) {
  isCallActive = true;
  isMuted = false;
  showScreen('active');
  startCallTimer();

  // 1. Prompt and request actual microphone stream
  const micOk = await setupMicrophoneStream();
  if (!micOk) {
    console.warn('Microphone stream could not be acquired.');
  }

  const selectedVoice = document.getElementById('voiceModelSelect').value;
  const greetingText = selectedVoice.startsWith('ta-')
    ? "வணக்கம் ஜெஃப்பி! Milo லைன்ல இருக்கேன். நம்ம சீன் பத்தி என்ன பேசலாம்?"
    : "Hey Jeffy! Milo is live. What scene or script idea are we developing?";

  appendTranscript('MILO AI', greetingText);
  updateOrbState('SPEAKING', 'pulse');

  // Greet user
  await playSpeechAudio(greetingText, selectedVoice);
  updateOrbState('LISTENING', 'idle');

  // 2. Start Speech Recognition & Audio Listening
  startVoicePipeline();
}

function showScreen(name) {
  document.getElementById('screenStandby').classList.toggle('hidden', name !== 'standby');
  document.getElementById('screenIncoming').classList.toggle('hidden', name !== 'incoming');
  document.getElementById('screenActive').classList.toggle('hidden', name !== 'active');
  if (window.lucide) lucide.createIcons();
}

function startCallTimer() {
  callSeconds = 0;
  clearInterval(callTimerInterval);
  const timerElem = document.getElementById('callTimer');
  callTimerInterval = setInterval(() => {
    callSeconds++;
    const mins = String(Math.floor(callSeconds / 60)).padStart(2, '0');
    const secs = String(callSeconds % 60).padStart(2, '0');
    if (timerElem) timerElem.textContent = `${mins}:${secs}`;
  }, 1000);
}

function updateOrbState(stateText, visual = 'idle') {
  const statusElem = document.getElementById('callOrbStatus');
  const ringElem = document.getElementById('orbWaveRing');
  const orb = document.getElementById('activeVoiceOrb');

  if (statusElem) statusElem.textContent = stateText;

  if (visual === 'pulse' || stateText === 'SPEAKING' || stateText === 'RECORDING') {
    if (ringElem) {
      ringElem.classList.remove('opacity-0');
      ringElem.classList.add('pulse-ring-active');
    }
    if (stateText === 'RECORDING') {
      orb.classList.add('border-rose-500', 'shadow-rose-500/30');
      orb.classList.remove('border-amber-400/40', 'shadow-amber-500/20');
    } else {
      orb.classList.remove('border-rose-500', 'shadow-rose-500/30');
      orb.classList.add('border-amber-400/40', 'shadow-amber-500/20');
    }
  } else {
    if (ringElem) {
      ringElem.classList.add('opacity-0');
      ringElem.classList.remove('pulse-ring-active');
    }
    orb.classList.remove('border-rose-500', 'shadow-rose-500/30');
    orb.classList.add('border-amber-400/40', 'shadow-amber-500/20');
  }
}

// =========================================================================
// REAL MICROPHONE STREAM & LIVE VISUALIZER
// =========================================================================
async function setupMicrophoneStream() {
  const blockedBanner = document.getElementById('micBlockedBanner');
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.warn('getUserMedia is not supported on this browser context.');
      if (blockedBanner) blockedBanner.classList.remove('hidden');
      return false;
    }

    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    if (blockedBanner) blockedBanner.classList.add('hidden');

    // Setup Web Audio Analyser
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx) {
      if (!audioContext) audioContext = new AudioCtx();
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }

      analyser = audioContext.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.5;

      const source = audioContext.createMediaStreamSource(micStream);
      source.connect(analyser);

      // Start live visualizer loop
      startVisualizerLoop();
    }

    // Initialize MediaRecorder for server fallback / Push-To-Talk
    initMediaRecorder();

    return true;
  } catch (err) {
    console.error('Microphone access error:', err);
    if (blockedBanner) blockedBanner.classList.remove('hidden');
    const micStatus = document.getElementById('micStatusText');
    if (micStatus) micStatus.textContent = '⚠️ Mic Access Denied';
    return false;
  }
}

function startVisualizerLoop() {
  if (!analyser) return;

  const dataArray = new Uint8Array(analyser.frequencyBinCount);
  const bars = [
    document.getElementById('wb-1'),
    document.getElementById('wb-2'),
    document.getElementById('wb-3'),
    document.getElementById('wb-4'),
    document.getElementById('wb-5'),
    document.getElementById('wb-6'),
    document.getElementById('wb-7'),
    document.getElementById('wb-8')
  ];

  const micStatus = document.getElementById('micStatusText');
  const micDot = document.getElementById('micDot');

  function renderFrame() {
    if (!isCallActive) return;

    analyser.getByteFrequencyData(dataArray);

    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    const avgVolume = sum / dataArray.length;

    // Scale wave bars to REAL audio input
    for (let i = 0; i < bars.length; i++) {
      if (bars[i]) {
        if (isMuted) {
          bars[i].style.height = '4px';
          bars[i].style.opacity = '0.3';
        } else if (isMiloSpeaking) {
          // Subtle rhythmic pulse while Milo is talking
          bars[i].style.height = `${8 + Math.sin(Date.now() / 150 + i) * 6}px`;
          bars[i].style.opacity = '0.7';
        } else {
          // User mic real-time height
          const binIndex = Math.min(i * 2, dataArray.length - 1);
          const val = dataArray[binIndex] || 0;
          const targetHeight = Math.max(6, Math.min(36, Math.round((val / 255) * 36)));
          bars[i].style.height = `${targetHeight}px`;
          bars[i].style.opacity = val > 20 ? '1' : '0.4';
        }
      }
    }

    // Voice Activity Detection & Indicator
    if (!isMuted && !isMiloSpeaking) {
      if (avgVolume > 20) {
        if (micStatus && !isManualRecording) micStatus.textContent = '🎙️ Hearing Voice...';
        if (micDot) micDot.className = 'w-2 h-2 rounded-full bg-emerald-400 scale-125 transition';

        // Auto-VAD triggering if speechRecognizer isn't running
        if (!speechRecognizer && mediaRecorder && mediaRecorder.state === 'inactive' && !isVadRecording && !isManualRecording) {
          triggerAutoVadRecord();
        }
      } else {
        if (micStatus && !isManualRecording && !isVadRecording) {
          micStatus.textContent = '🎧 Listening... (Speak now)';
        }
        if (micDot) micDot.className = 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse';
      }
    }

    visualizerAnimationId = requestAnimationFrame(renderFrame);
  }

  renderFrame();
}

// =========================================================================
// SPEECH RECOGNITION & SERVER MEDIARECORDER PIPELINE
// =========================================================================
function startVoicePipeline() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

  // Try Browser SpeechRecognition if supported, in secure context, and no previous hard errors
  if (SpeechRec && window.isSecureContext && speechRecFailCount < 2) {
    try {
      setupBrowserSpeechRecognition(SpeechRec);
      return;
    } catch (e) {
      console.warn('SpeechRecognition initialization failed; switching to Server Gemini STT:', e);
    }
  }

  // Fallback to Server-Side MediaRecorder Mode
  console.info('Using Server Gemini MediaRecorder STT Mode.');
  const micStatus = document.getElementById('micStatusText');
  if (micStatus) micStatus.textContent = '🎙️ Tap to Speak or Speak aloud';
}

function setupBrowserSpeechRecognition(SpeechRec) {
  speechRecognizer = new SpeechRec();
  speechRecognizer.continuous = true;
  speechRecognizer.interimResults = true;

  const selectedVoice = document.getElementById('voiceModelSelect').value;
  speechRecognizer.lang = selectedVoice.startsWith('ta-') ? 'ta-IN' : 'en-US';

  speechRecognizer.onresult = async (event) => {
    if (isMuted || !isCallActive || isMiloSpeaking) return;

    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    const bubble = document.getElementById('speechBubble');
    if (interimTranscript && bubble) {
      bubble.innerHTML = `<span class="text-amber-300 italic">"Hearing: ${interimTranscript}..."</span>`;
    }

    if (finalTranscript.trim()) {
      const spoken = finalTranscript.trim();
      appendTranscript('YOU', spoken);
      await processCallQuery(spoken);
    }
  };

  speechRecognizer.onerror = (e) => {
    console.warn('SpeechRec error:', e.error);
    speechRecFailCount++;
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed' || speechRecFailCount >= 2) {
      console.warn('Browser Speech blocked or failed repeatedly; falling back to Server STT.');
      try { speechRecognizer.stop(); } catch(err){}
      speechRecognizer = null;
      const micStatus = document.getElementById('micStatusText');
      if (micStatus) micStatus.textContent = '🎙️ Server Audio Active';
    }
  };

  speechRecognizer.onend = () => {
    if (isCallActive && !isMuted && !isMiloSpeaking && speechRecognizer && speechRecFailCount < 2) {
      try { speechRecognizer.start(); } catch (e) {}
    }
  };

  try {
    speechRecognizer.start();
  } catch (err) {
    console.warn('Failed to start speechRecognizer:', err);
    speechRecognizer = null;
  }
}

// MediaRecorder for Server-Side Gemini STT Fallback
function initMediaRecorder() {
  if (!micStream) return;
  try {
    const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
    let chosenMime = '';
    for (const m of mimeTypes) {
      if (MediaRecorder.isTypeSupported(m)) {
        chosenMime = m;
        break;
      }
    }

    mediaRecorder = new MediaRecorder(micStream, chosenMime ? { mimeType: chosenMime } : {});

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        recordedAudioChunks.push(e.data);
      }
    };

    mediaRecorder.onstop = async () => {
      if (recordedAudioChunks.length > 0) {
        const audioBlob = new Blob(recordedAudioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        recordedAudioChunks = [];
        await sendAudioBlobForTranscription(audioBlob);
      }
    };
  } catch (err) {
    console.warn('MediaRecorder initialization failed:', err);
  }
}

function triggerAutoVadRecord() {
  if (!mediaRecorder || mediaRecorder.state === 'recording' || isMiloSpeaking) return;

  isVadRecording = true;
  recordedAudioChunks = [];
  try {
    mediaRecorder.start();
  } catch(e) {
    return;
  }

  clearTimeout(vadSilenceTimeout);
  // Auto stop after 3.5s or on silence
  vadSilenceTimeout = setTimeout(() => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      try { mediaRecorder.stop(); } catch(e){}
    }
    isVadRecording = false;
  }, 3500);
}

// =========================================================================
// PUSH-TO-TALK / MANUAL HOLD-TO-SPEAK HANDLERS
// =========================================================================
function setupPushToTalkHandlers() {
  const pttBtn = document.getElementById('btnPushToTalk');
  const orb = document.getElementById('activeVoiceOrb');

  if (pttBtn) {
    // Touch Events for Mobile (with touchcancel safety)
    pttBtn.addEventListener('touchstart', (e) => {
      e.preventDefault();
      isTouchActive = true;
      startManualRecording();
    }, { passive: false });

    pttBtn.addEventListener('touchend', (e) => {
      e.preventDefault();
      isTouchActive = false;
      stopManualRecording();
    });

    pttBtn.addEventListener('touchcancel', () => {
      isTouchActive = false;
      stopManualRecording();
    });

    // Mouse Events for Desktop (suppressed if touch was active)
    pttBtn.addEventListener('mousedown', () => {
      if (!isTouchActive) startManualRecording();
    });

    pttBtn.addEventListener('mouseup', () => {
      if (!isTouchActive) stopManualRecording();
    });

    pttBtn.addEventListener('mouseleave', () => {
      if (isManualRecording && !isTouchActive) stopManualRecording();
    });
  }

  // Orb click also toggles recording
  if (orb) {
    orb.addEventListener('click', () => {
      unlockMobileAudio();
      if (!isManualRecording) {
        startManualRecording();
        const pttLabel = document.getElementById('pushToTalkLabel');
        if (pttLabel) pttLabel.textContent = 'Listening... Tap when done';
      } else {
        stopManualRecording();
      }
    });
  }
}

function startManualRecording() {
  if (isMiloSpeaking || !isCallActive) return;
  unlockMobileAudio();

  if (!mediaRecorder) {
    setupMicrophoneStream().then(() => {
      if (mediaRecorder) startManualRecording();
    });
    return;
  }

  isManualRecording = true;
  recordedAudioChunks = [];
  updateOrbState('RECORDING', 'pulse');

  const pttLabel = document.getElementById('pushToTalkLabel');
  const micStatus = document.getElementById('micStatusText');
  const bubble = document.getElementById('speechBubble');

  if (pttLabel) pttLabel.textContent = 'Recording... Release to send';
  if (micStatus) micStatus.textContent = '🔴 Recording Voice...';
  if (bubble) bubble.innerHTML = `<span class="text-rose-400 font-semibold animate-pulse">"Recording speech... release when done"</span>`;

  try {
    if (mediaRecorder.state === 'inactive') {
      mediaRecorder.start();
    }
  } catch(e) {
    console.warn('Failed to start manual recording:', e);
  }
}

function stopManualRecording() {
  if (!isManualRecording) return;
  isManualRecording = false;

  const pttLabel = document.getElementById('pushToTalkLabel');
  if (pttLabel) pttLabel.textContent = 'Hold or Tap to Speak';

  updateOrbState('THINKING', 'idle');

  const bubble = document.getElementById('speechBubble');
  if (bubble) bubble.innerHTML = `<span class="text-amber-400 italic">"Transcribing voice with Gemini..."</span>`;

  try {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
  } catch(e) {
    console.warn('Failed to stop manual recording:', e);
  }
}

// Send Audio Blob to Server STT Endpoint
async function sendAudioBlobForTranscription(blob) {
  const bubble = document.getElementById('speechBubble');

  if (!blob || blob.size < 500) {
    updateOrbState('LISTENING', 'idle');
    if (bubble) bubble.innerHTML = `<span>"Ready to brainstorm, Jeffy. Speak freely!"</span>`;
    return;
  }

  updateOrbState('THINKING', 'idle');
  const formData = new FormData();
  formData.append('audio', blob, 'recording.webm');

  try {
    const res = await fetch('/api/voice/transcribe', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (data.success && data.text && data.text.trim()) {
      const spoken = data.text.trim();
      appendTranscript('YOU', spoken);
      await processCallQuery(spoken);
    } else {
      console.log('No speech detected in audio slice.');
      updateOrbState('LISTENING', 'idle');
      if (bubble) bubble.innerHTML = `<span>"Didn't catch that. Tap and speak again, Jeffy!"</span>`;
    }
  } catch (err) {
    console.error('Transcription error:', err);
    updateOrbState('LISTENING', 'idle');
    if (bubble) bubble.innerHTML = `<span>"Network error transcribing audio."</span>`;
  }
}

// =========================================================================
// QUERY PROCESSING & Milo Spoken Response
// =========================================================================
async function processCallQuery(queryText) {
  isMiloSpeaking = true;
  updateOrbState('THINKING', 'idle');
  const bubble = document.getElementById('speechBubble');
  if (bubble) bubble.innerHTML = `<span class="italic text-slate-400">Milo is thinking...</span>`;

  const selectedVoice = document.getElementById('voiceModelSelect').value;

  try {
    const res = await fetch('/api/voice/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: queryText, voice: selectedVoice })
    });
    const data = await res.json();

    if (data.reply) {
      appendTranscript('MILO AI', data.reply);
      if (bubble) bubble.innerHTML = `<span>"${data.clean_speech.substring(0, 85)}..."</span>`;

      updateOrbState('SPEAKING', 'pulse');
      await playSpeechAudio(data.clean_speech, selectedVoice);
      updateOrbState('LISTENING', 'idle');
    }
  } catch (err) {
    console.error('Call query error:', err);
    updateOrbState('LISTENING', 'idle');
  } finally {
    isMiloSpeaking = false;
  }
}

function playSpeechAudio(text, voice) {
  return new Promise((resolve) => {
    if (isSpeakerMuted) {
      return resolve();
    }

    const speaker = document.getElementById('miloSpeakerAudio');
    if (!speaker) {
      return resolve();
    }

    const url = `/api/voice/tts?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}&format=opus`;

    speaker.src = url;
    speaker.onended = () => resolve();
    speaker.onerror = (e) => {
      console.warn('Audio playback error:', e);
      resolve();
    };

    speaker.play().catch((e) => {
      console.warn('Audio auto-play prevented by mobile browser:', e);
      resolve();
    });
  });
}

function endActiveCall(notifyBackend = true) {
  isCallActive = false;
  isMiloSpeaking = false;
  isManualRecording = false;
  isVadRecording = false;

  clearInterval(callTimerInterval);
  cancelAnimationFrame(visualizerAnimationId);
  stopRingtone();

  const speaker = document.getElementById('miloSpeakerAudio');
  if (speaker) {
    try { speaker.pause(); speaker.currentTime = 0; } catch (e) {}
  }

  if (speechRecognizer) {
    try { speechRecognizer.stop(); } catch (e) {}
    speechRecognizer = null;
  }

  if (mediaRecorder && mediaRecorder.state === 'recording') {
    try { mediaRecorder.stop(); } catch (e) {}
  }

  if (micStream) {
    try {
      micStream.getTracks().forEach((t) => t.stop());
    } catch(e){}
    micStream = null;
  }

  if (audioContext && audioContext.state !== 'closed') {
    try { audioContext.close(); } catch(e){}
    audioContext = null;
  }

  if (notifyBackend && callSocket && callSocket.readyState === WebSocket.OPEN) {
    callSocket.send(JSON.stringify({ type: 'call_ended' }));
  }

  showScreen('standby');
}

function toggleCallMute() {
  isMuted = !isMuted;

  // Real Hardware Microphone Track Mute
  if (micStream) {
    micStream.getAudioTracks().forEach((track) => {
      track.enabled = !isMuted;
    });
  }

  const btn = document.getElementById('btnMute');
  if (btn) {
    btn.classList.toggle('bg-rose-950', isMuted);
    btn.classList.toggle('text-rose-400', isMuted);
    btn.classList.toggle('border-rose-500/30', isMuted);

    // Fix Lucide Icon SVG replacement bug
    btn.innerHTML = `<i data-lucide="${isMuted ? 'mic-off' : 'mic'}" class="w-6 h-6"></i>`;
    if (window.lucide) lucide.createIcons({ root: btn });
  }

  const micStatus = document.getElementById('micStatusText');
  if (micStatus) {
    micStatus.textContent = isMuted ? '🔇 Microphone Muted' : '🎧 Listening... (Speak now)';
  }
}

function toggleSpeaker() {
  isSpeakerMuted = !isSpeakerMuted;
  const btn = document.getElementById('btnSpeaker');
  const speaker = document.getElementById('miloSpeakerAudio');

  if (speaker) {
    speaker.muted = isSpeakerMuted;
  }

  if (btn) {
    btn.classList.toggle('text-amber-400', !isSpeakerMuted);
    btn.classList.toggle('text-rose-400', isSpeakerMuted);

    // Fix Lucide Icon SVG replacement bug
    btn.innerHTML = `<i data-lucide="${isSpeakerMuted ? 'volume-x' : 'volume-2'}" class="w-6 h-6"></i>`;
    if (window.lucide) lucide.createIcons({ root: btn });
  }
}

function appendTranscript(speaker, text) {
  const list = document.getElementById('transcriptList');
  if (!list) return;

  const item = document.createElement('div');
  item.className = 'p-2.5 rounded-xl bg-noir-850 border border-white/5';
  const color = speaker === 'YOU' ? 'text-cyan-400' : 'text-amber-400';
  item.innerHTML = `
    <span class="${color} font-mono text-[10px] block font-bold mb-0.5">${speaker}</span>
    <span class="text-slate-300">${text}</span>
  `;
  list.appendChild(item);
  list.scrollTop = list.scrollHeight;
}

function toggleTranscriptDrawer() {
  const drawer = document.getElementById('transcriptDrawer');
  if (drawer) {
    drawer.classList.toggle('hidden');
    if (window.lucide) lucide.createIcons();
  }
}
