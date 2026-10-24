// Kino Cinema Studio — Frontend Controller

let activeTab = 'corkboard';
let currentProjectSlug = 'project_mirage';

// Sample scene contents for instant switching
const sampleScenes = {
  1: `EXT. DOCK PIER - NIGHT

Torrential monsoon rain hammers down against rusted shipping containers. White lightning tears through the horizon, casting momentary stark silhouettes across the harbor.

VIKRAM (38) lies half-submerged in dirty seawater. Blood seeps from a laceration above his temple, dissolving into the foam.

He awakens with a violent gasp. His fingers claw into the slick timber pilings. 

His sidearm, a Glock 19, lies five feet away, its slide locked back. Empty. 

Around his wrist hangs a pair of military dog tags bearing the name: 'K. RATHORE - KIA'. He touches his own face. Confusion and panic register in his eyes. He has no idea whose dog tags they are—or who he is.`,

  2: `INT. DERELICT SAFE HOUSE - NIGHT

Water drips from a cracked ceiling into a galvanized bucket with rhythmic metallic pings.

Vikram sits on an overturned crate, wrapping duct tape tightly around his bleeding ribs. He winces in silence.

On a rickety table sits a black burner phone. It has no SIM card.

Suddenly, the screen flashes amber. A harsh digital buzzer vibrates through the wood.

Vikram stares at it. The caller ID displays: 'UNKNOWN TRANSMISSION - PRIORITY RED'.

He lifts the receiver to his ear without speaking.

CHIEF MENON (V.O.)
(distorted, cold)
If you are listening to this frequency, agent, your extraction failed. You have been classified as compromised. Clean-up units have been dispatched to Sector 4. Good luck.

The line goes dead.`,

  3: `EXT. RAILWAY FOOTBRIDGE - MIDNIGHT

High above the electrified railway lines, steam from passing freight trains rises into the drizzle.

Vikram stands by the iron railing. In his left hand, he holds his leather government credentials and intelligence badge.

He strikes a vintage lighter. The flame catches the corner of the badge.

He drops the burning identification into the void below. As it flutters down into the sparks of an oncoming cargo engine, Vikram's posture stiffens.

The amnesiac cop is gone. The hunter takes over.`,

  4: `INT. DERELICT DOCK WAREHOUSE - NIGHT

Rain hammers the rusted corrugated roof like shrapnel. Steam billows from fractured boiler conduits.

VIKRAM (38) stands motionless behind a row of wooden shipping crates. His left shoulder is soaked in dark red; a Glock 19 rests in his palm. His knuckles are white with tension.

Across the waterlogged concrete expanse, RUDRA (45) stands in the single beam of halogen floodlight. He takes a slow drag from a battered silver cigarette case.

RUDRA
(flicking ash into the puddles)
You are twenty minutes early, Vikram. In our line of work, eager men usually end up floating face-down before dawn.

VIKRAM
Where is the second drive, Rudra?

RUDRA
Still asking schoolboy questions. You think the Bureau wanted you to survive tonight? Look up at the gantry, officer. 

Vikram does not look up. But a solitary red laser diode glides across his chest, locking directly over his heart.`,

  5: `INT. MUMBAI CITY HALL - DAY (MIDPOINT)

Chaos erupts across the grand marble rotunda. Sirens wail in three distinct frequencies.

The emergency sirens cease abruptly. Every light fixture snaps dark. The massive backup generators fail simultaneously.

In the sudden pitch black, emerald night-vision goggles click on around the perimeter balconies.

Vikram, disguised as a police tactical captain, grabs the server drive from the vault podium. But when the emergency strobe kicks in, he realizes the SWAT squad surrounding him is not the state police. 

They are Rudra's private syndicate contractors. And they are saluting him.`
};

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  loadProjects();
  loadIdeasVault();
  loadCharactersVault();

  // Check URL params or hash for initial tab
  const urlParams = new URLSearchParams(window.location.search);
  const initialTab = urlParams.get('tab') || window.location.hash.replace('#', '');
  if (initialTab && ['corkboard', 'screenplay', 'shotlist', 'characters', 'ideas', 'voice'].includes(initialTab)) {
    switchTab(initialTab);
    if (initialTab === 'voice' && urlParams.get('autocall') === '1') {
      setTimeout(() => {
        if (!isVoiceConnected) toggleVoiceCall();
      }, 600);
    }
  }
});

function switchTab(tabId) {
  activeTab = tabId;
  const tabs = ['corkboard', 'screenplay', 'shotlist', 'characters', 'ideas', 'voice'];
  tabs.forEach(t => {
    const view = document.getElementById(`view-${t}`);
    const navBtn = document.getElementById(`tab-${t}`);
    if (t === tabId) {
      if (view) view.classList.remove('hidden');
      if (navBtn) {
        navBtn.classList.add('active');
        navBtn.classList.remove('text-slate-400');
        navBtn.classList.add('text-amber-400');
      }
    } else {
      if (view) view.classList.add('hidden');
      if (navBtn) {
        navBtn.classList.remove('active');
        navBtn.classList.remove('text-amber-400');
        navBtn.classList.add('text-slate-400');
      }
    }
  });

  if (window.lucide) {
    lucide.createIcons();
  }
}

async function loadProjects() {
  try {
    const res = await fetch('/api/projects');
    const data = await res.json();
    const select = document.getElementById('projectSelect');
    if (data.projects && data.projects.length > 0) {
      select.innerHTML = '';
      data.projects.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.slug;
        opt.textContent = `${p.title} (${p.slug === currentProjectSlug ? 'Active' : 'In Dev'})`;
        select.appendChild(opt);
      });
      select.value = currentProjectSlug;
    }
  } catch (err) {
    console.error('Failed to load projects:', err);
  }
}

function loadSceneToEditor(sceneNum) {
  const editor = document.getElementById('screenplayEditor');
  if (sampleScenes[sceneNum]) {
    editor.value = sampleScenes[sceneNum];
  }
  switchTab('screenplay');
  showToast(`Loaded Scene ${sceneNum} into Screenplay Studio!`);
}

function insertScreenplayTag(tag) {
  const editor = document.getElementById('screenplayEditor');
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  const text = editor.value;
  editor.value = text.substring(0, start) + "\n\n" + tag + text.substring(end);
  editor.focus();
  editor.selectionStart = editor.selectionEnd = start + tag.length + 2;
}

async function saveCurrentScript() {
  const content = document.getElementById('screenplayEditor').value;
  try {
    const res = await fetch('/api/project/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        slug: currentProjectSlug,
        filename: 'SceneDraft.md',
        content: content
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Scene draft saved to Obsidian Cinema Vault!');
    } else {
      showToast('Failed to save scene.');
    }
  } catch (e) {
    showToast('Network error saving scene.');
  }
}

async function runDoctorOnCurrentScript() {
  const content = document.getElementById('screenplayEditor').value.trim();
  const btn = document.getElementById('doctorAnalyzeBtn');
  const output = document.getElementById('doctorOutputArea');

  if (!content) {
    showToast('Please type or load a scene first.');
    return;
  }

  btn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Diagnosing...</span>`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch('/api/ai/doctor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scene_pitch: content })
    });
    const data = await res.json();

    if (data.success) {
      output.innerHTML = `
        <div class="bg-noir-850 border border-emerald-500/40 rounded-xl p-4">
          <div class="flex items-center space-x-2 text-xs font-bold text-emerald-400 uppercase tracking-wide mb-2">
            <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i>
            <span>Kino Script Doctor Diagnosis</span>
          </div>
          <div class="prose prose-invert prose-sm text-slate-200">
            ${marked.parse(data.result)}
          </div>
        </div>
      `;
      showToast('Script Doctor analysis complete!');
    } else {
      showToast('Doctor failed: ' + data.error);
    }
  } catch (err) {
    showToast('Error contacting Kino engine.');
  } finally {
    btn.innerHTML = `<i data-lucide="sparkles" class="w-3.5 h-3.5"></i><span>Re-Analyze Scene</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

async function askKinoCustom() {
  const input = document.getElementById('kinoPromptInput');
  const prompt = input.value.trim();
  if (!prompt) return;

  const currentScript = document.getElementById('screenplayEditor').value;
  const combined = `Screenplay context:\n${currentScript.substring(0, 300)}...\n\nDirector's Question:\n${prompt}`;

  input.value = '';
  showToast('Consulting Kino Director...');

  try {
    const res = await fetch('/api/ai/doctor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scene_pitch: combined })
    });
    const data = await res.json();
    if (data.success) {
      const output = document.getElementById('doctorOutputArea');
      const card = document.createElement('div');
      card.className = "bg-noir-850 border border-amber-500/40 rounded-xl p-4 mb-3";
      card.innerHTML = `
        <div class="text-xs font-bold text-amber-400 mb-1">Director's Query: "${prompt}"</div>
        <div class="prose prose-invert prose-xs text-slate-300">${marked.parse(data.result)}</div>
      `;
      output.prepend(card);
    }
  } catch (e) {
    showToast('Failed to consult Kino.');
  }
}

async function loadIdeasVault() {
  try {
    const res = await fetch('/api/ideas');
    const data = await res.json();
    if (data.ideas && data.ideas.length > 0) {
      const first = data.ideas[0];
      const card = document.getElementById('ideaOutputCard');
      card.innerHTML = `
        <div class="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
          <span class="text-xs font-mono text-amber-400 uppercase tracking-wider">Obsidian Vault: ${first.filename}</span>
          <span class="text-xs text-slate-400">${first.modified}</span>
        </div>
        <div>${marked.parse(first.content)}</div>
      `;
    }
  } catch (e) {
    console.error('Failed to load ideas:', e);
  }
}

async function developNewIdea() {
  const input = document.getElementById('ideaInput');
  const idea = input.value.trim();
  if (!idea) {
    showToast('Please type a premise first.');
    return;
  }

  const btn = document.getElementById('developIdeaBtn');
  btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Generating Treatment...</span>`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch('/api/ai/idea', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_idea: idea })
    });
    const data = await res.json();
    if (data.success) {
      const card = document.getElementById('ideaOutputCard');
      card.innerHTML = `
        <div class="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
          <span class="text-xs font-mono text-amber-400 uppercase tracking-wider">💡 Newly Developed Treatment</span>
          <span class="text-xs text-emerald-400">Saved to Obsidian/Cinema/Ideas</span>
        </div>
        <div>${marked.parse(data.result)}</div>
      `;
      showToast('Treatment generated and saved to Obsidian Vault!');
      input.value = '';
    } else {
      showToast('Error: ' + data.error);
    }
  } catch (err) {
    showToast('Failed to develop idea.');
  } finally {
    btn.innerHTML = `<i data-lucide="flame" class="w-4 h-4"></i><span>Develop Treatment</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

async function loadCharactersVault() {
  try {
    const res = await fetch('/api/characters');
    const data = await res.json();
    if (data.characters && data.characters.length > 0) {
      // additional characters can be appended if present
    }
  } catch (e) {
    console.error('Failed to load characters:', e);
  }
}

function openNewProjectModal() {
  document.getElementById('newProjectModal').classList.remove('hidden');
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
}

async function submitNewProject() {
  const title = document.getElementById('newProjectTitle').value.trim();
  if (!title) return;

  try {
    const res = await fetch('/api/project/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Film Project '${title}' initialized!`);
      closeModal('newProjectModal');
      await loadProjects();
    }
  } catch (e) {
    showToast('Failed to create project.');
  }
}

function exportScript() {
  const content = document.getElementById('screenplayEditor').value;
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentProjectSlug}_Screenplay.fountain`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Screenplay exported as .fountain file!');
}

function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'kino-toast';
  toast.innerHTML = `<i data-lucide="info" class="w-4 h-4 text-amber-400"></i><span>${msg}</span>`;
  document.body.appendChild(toast);
  if (window.lucide) lucide.createIcons();
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// =========================================================================
// LIVEKIT WEBRTC REAL-TIME VOICE STUDIO
// =========================================================================

let livekitRoom = null;
let isVoiceConnected = false;
let isMicMuted = false;
let voiceRecognition = null;
let currentVoiceAudio = null;
let waveAnimationInterval = null;

async function toggleVoiceCall() {
  if (isVoiceConnected) {
    disconnectVoiceCall();
  } else {
    await startVoiceCall();
  }
}

async function startVoiceCall() {
  const orb = document.getElementById('voiceOrb');
  const orbLabel = document.getElementById('voiceOrbLabel');
  const connectBtn = document.getElementById('connectBtnLabel');
  const subtext = document.getElementById('voiceStatusSubtext');
  const ring = document.getElementById('orbRing');

  orbLabel.textContent = 'CONNECTING...';
  subtext.textContent = 'Connecting to LiveKit WebRTC server at ws://127.0.0.1:7880...';

  try {
    const res = await fetch('/api/voice/token');
    const data = await res.json();
    if (!data.token) {
      showToast('Failed to retrieve LiveKit token.');
      resetVoiceUI();
      return;
    }

    if (window.LivekitClient) {
      try {
        livekitRoom = new LivekitClient.Room({
          adaptiveStream: true,
          dynacast: true,
        });

        await livekitRoom.connect(data.url, data.token);
        await livekitRoom.localParticipant.setMicrophoneEnabled(true);
        console.log('Connected to LiveKit room:', data.room);
      } catch (e) {
        console.warn('LiveKit local WebRTC audio fallback active:', e);
      }
    }

    isVoiceConnected = true;
    orb.classList.add('border-emerald-500', 'shadow-emerald-500/20');
    orb.classList.remove('border-amber-500/30', 'shadow-amber-500/10');
    ring.classList.remove('opacity-0');
    ring.classList.add('border-emerald-400/40');
    orbLabel.textContent = 'LISTENING';
    connectBtn.textContent = 'End Call';
    document.getElementById('voiceConnectBtn').className = "px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition shadow-lg shadow-rose-600/20 flex items-center gap-1.5";
    subtext.textContent = 'LiveKit WebRTC active! Speak freely. Milo & Kino are listening.';

    startAudioWaveAnimation();
    initSpeechRecognition();
    showToast('LiveKit WebRTC Voice connected!');

  } catch (err) {
    console.error('Voice connection error:', err);
    showToast('LiveKit connection error: ' + err.message);
    resetVoiceUI();
  }
}

function disconnectVoiceCall() {
  if (livekitRoom) {
    try { livekitRoom.disconnect(); } catch(e){}
    livekitRoom = null;
  }
  if (voiceRecognition) {
    try { voiceRecognition.stop(); } catch(e){}
    voiceRecognition = null;
  }
  if (currentVoiceAudio) {
    currentVoiceAudio.pause();
    currentVoiceAudio = null;
  }
  isVoiceConnected = false;
  stopAudioWaveAnimation();
  resetVoiceUI();
  showToast('Voice call ended.');
}

function resetVoiceUI() {
  const orb = document.getElementById('voiceOrb');
  const orbLabel = document.getElementById('voiceOrbLabel');
  const connectBtn = document.getElementById('connectBtnLabel');
  const subtext = document.getElementById('voiceStatusSubtext');
  const ring = document.getElementById('orbRing');

  orb.className = "relative w-48 h-48 rounded-full bg-gradient-to-tr from-amber-600/20 via-amber-500/10 to-noir-850 border border-amber-500/30 flex items-center justify-center shadow-2xl shadow-amber-500/10 transition-all duration-300 group cursor-pointer";
  ring.className = "absolute inset-0 rounded-full border border-amber-400/20 scale-110 animate-ping opacity-0";
  orbLabel.textContent = 'CONNECT';
  connectBtn.textContent = 'Start Call';
  document.getElementById('voiceConnectBtn').className = "px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-noir-950 text-xs font-bold transition shadow-lg shadow-amber-500/20 flex items-center gap-1.5";
  subtext.textContent = 'Tap the orb to start live voice talk with Milo & Kino. Full conversational turn-taking with zero awkward pauses.';
}

function toggleMute() {
  isMicMuted = !isMicMuted;
  const label = document.getElementById('muteBtnLabel');
  const btn = document.getElementById('voiceMuteBtn');

  if (livekitRoom && livekitRoom.localParticipant) {
    try { livekitRoom.localParticipant.setMicrophoneEnabled(!isMicMuted); } catch(e){}
  }

  if (isMicMuted) {
    label.textContent = 'Unmute';
    btn.classList.add('bg-rose-950', 'text-rose-300', 'border-rose-500/30');
    showToast('Microphone muted.');
  } else {
    label.textContent = 'Mute';
    btn.classList.remove('bg-rose-950', 'text-rose-300', 'border-rose-500/30');
    showToast('Microphone unmuted.');
  }
}

function initSpeechRecognition() {
  // Prevent WebKitGTK WebProcess crash: WebKitGTK defines webkitSpeechRecognition stub without backend
  const isWebKitEngine = !window.chrome && navigator.userAgent.includes('WebKit');
  if (isWebKitEngine) {
    console.info('WebKitGTK environment detected: Voice recognition uses LiveKit WebRTC or manual audio.');
    return;
  }

  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    console.warn('Web Speech API not supported; fallback to text query.');
    return;
  }

  try {
    voiceRecognition = new SpeechRec();
    voiceRecognition.continuous = true;
    voiceRecognition.interimResults = false;
    voiceRecognition.lang = 'en-US';

    voiceRecognition.onresult = async (event) => {
      if (isMicMuted) return;
      const lastResultIndex = event.results.length - 1;
      const spokenText = event.results[lastResultIndex][0].transcript.trim();

      if (spokenText) {
        appendVoiceMessage('YOU', spokenText);
        await processSpokenQuery(spokenText);
      }
    };

    voiceRecognition.onerror = (e) => {
      console.warn('Speech recognition status:', e.error);
    };

    voiceRecognition.onend = () => {
      if (isVoiceConnected && !isMicMuted) {
        try { voiceRecognition.start(); } catch(e){}
      }
    };

    voiceRecognition.start();
  } catch (e) {
    console.warn('Speech recognition start failed or unavailable:', e);
  }
}

async function processSpokenQuery(queryText) {
  const orbLabel = document.getElementById('voiceOrbLabel');
  orbLabel.textContent = 'THINKING...';

  const selectedVoice = document.getElementById('voiceSelect').value;

  try {
    const res = await fetch('/api/voice/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: queryText, voice: selectedVoice })
    });
    const data = await res.json();

    if (data.reply) {
      appendVoiceMessage('MILO VOICE', data.reply);
      orbLabel.textContent = 'SPEAKING...';

      // Request Ogg/Opus format: universally decoded by GStreamer (opusdec) and Chromium
      const audioUrl = `/api/voice/tts?text=${encodeURIComponent(data.clean_speech)}&voice=${encodeURIComponent(selectedVoice)}&format=opus`;
      if (currentVoiceAudio) {
        try { currentVoiceAudio.pause(); } catch(e){}
      }

      currentVoiceAudio = new Audio(audioUrl);
      currentVoiceAudio.onended = () => {
        orbLabel.textContent = isVoiceConnected ? 'LISTENING' : 'CONNECT';
      };
      currentVoiceAudio.onerror = (e) => {
        console.warn('Audio playback error:', e);
        orbLabel.textContent = isVoiceConnected ? 'LISTENING' : 'CONNECT';
      };

      try {
        await currentVoiceAudio.play();
      } catch (playErr) {
        console.warn('Audio auto-play prevented:', playErr);
        orbLabel.textContent = isVoiceConnected ? 'LISTENING' : 'CONNECT';
      }
    }
  } catch (err) {
    console.error('Error processing query:', err);
    orbLabel.textContent = isVoiceConnected ? 'LISTENING' : 'CONNECT';
  }
}

async function sendManualVoiceQuery() {
  const input = document.getElementById('voiceTextInput');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  appendVoiceMessage('YOU', text);
  await processSpokenQuery(text);
}

function appendVoiceMessage(sender, text) {
  const area = document.getElementById('voiceTranscriptArea');
  const msg = document.createElement('div');
  const isUser = sender === 'YOU';
  msg.className = `p-3 rounded-xl border ${isUser ? 'bg-amber-500/10 border-amber-500/30 text-amber-200' : 'bg-noir-850 border-white/5 text-slate-200'}`;
  msg.innerHTML = `
    <div class="flex items-center justify-between mb-1">
      <span class="font-bold font-mono text-[10px] ${isUser ? 'text-amber-400' : 'text-cyan-400'}">${sender}</span>
      <span class="text-[10px] text-slate-500">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
    </div>
    <div class="leading-relaxed">${window.marked ? marked.parse(text) : text}</div>
  `;
  area.appendChild(msg);
  area.scrollTop = area.scrollHeight;
}

function clearVoiceTranscript() {
  const area = document.getElementById('voiceTranscriptArea');
  area.innerHTML = `
    <div class="p-3 rounded-xl bg-noir-850 border border-white/5 text-slate-300">
      <span class="text-amber-400 font-bold font-mono text-[10px] block mb-1">MILO VOICE AI</span>
      Transcript cleared. Standing by on LiveKit WebRTC.
    </div>
  `;
}

function startAudioWaveAnimation() {
  const bars = document.querySelectorAll('.wave-bar');
  if (waveAnimationInterval) clearInterval(waveAnimationInterval);

  waveAnimationInterval = setInterval(() => {
    bars.forEach(bar => {
      const height = Math.floor(Math.random() * 32) + 6;
      bar.style.height = `${height}px`;
    });
  }, 120);
}

function stopAudioWaveAnimation() {
  if (waveAnimationInterval) clearInterval(waveAnimationInterval);
  const bars = document.querySelectorAll('.wave-bar');
  const defaults = [12, 20, 32, 40, 24, 16, 8];
  bars.forEach((bar, idx) => {
    bar.style.height = `${defaults[idx] || 12}px`;
  });
}
