package ai.milo.nativecall;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.media.Ringtone;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Vibrator;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.Manifest;

import java.util.Locale;

/**
 * Pure 100% Native Android Application for Milo AI.
 * Zero WebView. Custom 2D Canvas Audio Visualizer, Director Mode Chips,
 * Voice Selector Modal, and Real-Time Voice Communication.
 */
public class MainActivity extends Activity implements AudioEngine.AudioListener {
    private static final int PERMISSION_REQ_CODE = 2001;

    private LinearLayout layoutStandby;
    private LinearLayout layoutIncoming;
    private LinearLayout layoutActive;

    private PulsingOrbView pulsingOrb;
    private WaveformVisualizerView waveformVisualizer;
    private TextView txtCallTimer;
    private TextView txtSpeechBubble;
    private TextView txtMuteIcon;
    private TextView txtSpeakerIcon;
    private TextView txtCurrentVoiceName;
    private TextView txtSessionHint;
    private TextView txtActiveCallTitle;
    private TextView txtActiveCallSubtitle;
    private Button btnPushToTalk;

    // Companion & Subagent Modes
    private TextView chipMilo;
    private TextView chipKinoStory;
    private TextView chipCharacters;
    private TextView chipShotlist;

    private enum CompanionMode {
        MILO_MAIN, KINO_STORY, KINO_CHARACTERS, KINO_SHOTLIST
    }
    private CompanionMode currentMode = CompanionMode.MILO_MAIN;

    private AudioEngine audioEngine;
    private NetworkClient networkClient;

    private Handler timerHandler = new Handler(Looper.getMainLooper());
    private int callSeconds = 0;
    private boolean isCallActive = false;
    private boolean isMuted = false;

    private Ringtone ringtone;
    private Vibrator vibrator;

    private final String[] VOICE_DISPLAY_NAMES = new String[]{
        "Valluvar (Tamil — Default)",
        "Christopher (Director / Hollywood)",
        "Prabhat (Indian English)",
        "Neerja (Expressive Female)"
    };

    private final String[] VOICE_KEYS = new String[]{
        "ta-IN-ValluvarNeural",
        "en-US-ChristopherNeural",
        "en-IN-PrabhatNeural",
        "en-IN-NeerjaExpressiveNeural"
    };

    private int selectedVoiceIndex = 0; // Default: Valluvar (Tamil)

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Hardware Fullscreen & Immersive Dark Styling
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            getWindow().setStatusBarColor(Color.parseColor("#040508"));
            getWindow().setNavigationBarColor(Color.parseColor("#040508"));
        }

        setContentView(R.layout.activity_main);

        // Initialize Native Components
        audioEngine = new AudioEngine(this, this);
        networkClient = new NetworkClient();
        vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);

        initViews();
        setupDirectorChips();
        checkPermissions();
    }

    private void initViews() {
        layoutStandby = findViewById(R.id.layoutStandby);
        layoutIncoming = findViewById(R.id.layoutIncoming);
        layoutActive = findViewById(R.id.layoutActive);

        pulsingOrb = findViewById(R.id.pulsingOrb);
        waveformVisualizer = findViewById(R.id.waveformVisualizer);
        txtCallTimer = findViewById(R.id.txtCallTimer);
        txtSpeechBubble = findViewById(R.id.txtSpeechBubble);
        txtMuteIcon = findViewById(R.id.txtMuteIcon);
        txtSpeakerIcon = findViewById(R.id.txtSpeakerIcon);
        txtCurrentVoiceName = findViewById(R.id.txtCurrentVoiceName);
        txtSessionHint = findViewById(R.id.txtSessionHint);
        txtActiveCallTitle = findViewById(R.id.txtActiveCallTitle);
        txtActiveCallSubtitle = findViewById(R.id.txtActiveCallSubtitle);
        btnPushToTalk = findViewById(R.id.btnPushToTalk);

        chipMilo = findViewById(R.id.chipMilo);
        chipKinoStory = findViewById(R.id.chipKinoStory);
        chipCharacters = findViewById(R.id.chipCharacters);
        chipShotlist = findViewById(R.id.chipShotlist);

        // Primary Call Button (Standby)
        findViewById(R.id.btnStartCall).setOnClickListener(v -> startCallSession());

        // Test Ring Button (Standby)
        findViewById(R.id.btnSimulateRing).setOnClickListener(v -> triggerIncomingRing("Screenplay Beat Doctoring"));

        // Modern Voice Selector Card Click -> Shows Native Modal
        findViewById(R.id.btnSelectVoiceCard).setOnClickListener(v -> showVoiceSelectionDialog());

        // Ringing Screen Actions
        findViewById(R.id.btnAcceptCall).setOnClickListener(v -> acceptCallSession());
        findViewById(R.id.btnDeclineCall).setOnClickListener(v -> declineCallSession());

        // Active Call Controls
        findViewById(R.id.btnEndCall).setOnClickListener(v -> endCallSession());
        findViewById(R.id.btnMute).setOnClickListener(v -> toggleMute());
        findViewById(R.id.btnSpeaker).setOnClickListener(v -> toggleSpeaker());

        // Push-to-Talk Touch Listeners
        btnPushToTalk.setOnTouchListener((v, event) -> {
            switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN:
                    pulsingOrb.setState(PulsingOrbView.State.RECORDING);
                    btnPushToTalk.setText("🔴 Recording... Release to send");
                    audioEngine.startManualSpeechCapture();
                    return true;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    btnPushToTalk.setText("🎙️ Hold or Tap to Speak");
                    pulsingOrb.setState(PulsingOrbView.State.THINKING);
                    byte[] wav = audioEngine.stopManualSpeechCapture();
                    if (wav != null && wav.length > 500) {
                        handleRecordedSpeech(wav);
                    } else {
                        pulsingOrb.setState(PulsingOrbView.State.LISTENING);
                    }
                    return true;
            }
            return false;
        });

        // Tapping Orb also toggles speech
        pulsingOrb.setOnClickListener(v -> {
            if (pulsingOrb.getState() == PulsingOrbView.State.RECORDING) {
                pulsingOrb.setState(PulsingOrbView.State.THINKING);
                byte[] wav = audioEngine.stopManualSpeechCapture();
                if (wav != null) handleRecordedSpeech(wav);
            } else if (pulsingOrb.getState() == PulsingOrbView.State.LISTENING) {
                pulsingOrb.setState(PulsingOrbView.State.RECORDING);
                audioEngine.startManualSpeechCapture();
                Toast.makeText(this, "Recording speech... tap orb when done", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void setupDirectorChips() {
        chipMilo.setOnClickListener(v -> selectMode(CompanionMode.MILO_MAIN));
        chipKinoStory.setOnClickListener(v -> selectMode(CompanionMode.KINO_STORY));
        chipCharacters.setOnClickListener(v -> selectMode(CompanionMode.KINO_CHARACTERS));
        chipShotlist.setOnClickListener(v -> selectMode(CompanionMode.KINO_SHOTLIST));
        selectMode(CompanionMode.MILO_MAIN); // MILO MAIN AI IS DEFAULT!
    }

    private void selectMode(CompanionMode mode) {
        this.currentMode = mode;

        // Reset all chips
        chipMilo.setBackgroundResource(R.drawable.bg_chip_normal);
        chipMilo.setTextColor(Color.parseColor("#94a3b8"));
        chipKinoStory.setBackgroundResource(R.drawable.bg_chip_normal);
        chipKinoStory.setTextColor(Color.parseColor("#94a3b8"));
        chipCharacters.setBackgroundResource(R.drawable.bg_chip_normal);
        chipCharacters.setTextColor(Color.parseColor("#94a3b8"));
        chipShotlist.setBackgroundResource(R.drawable.bg_chip_normal);
        chipShotlist.setTextColor(Color.parseColor("#94a3b8"));

        // Highlight selected chip & update titles
        switch (mode) {
            case MILO_MAIN:
                chipMilo.setBackgroundResource(R.drawable.bg_chip_selected);
                chipMilo.setTextColor(Color.parseColor("#fbbf24"));
                txtSessionHint.setText("Session: Milo Personal AI Desktop Companion & Executive Co-Pilot.");
                if (txtActiveCallTitle != null) txtActiveCallTitle.setText("Milo AI");
                if (txtActiveCallSubtitle != null) {
                    txtActiveCallSubtitle.setText("Personal AI Desktop Companion");
                    txtActiveCallSubtitle.setTextColor(Color.parseColor("#fbbf24"));
                }
                break;
            case KINO_STORY:
                chipKinoStory.setBackgroundResource(R.drawable.bg_chip_selected);
                chipKinoStory.setTextColor(Color.parseColor("#fbbf24"));
                txtSessionHint.setText("Subagent: Kino Script Doctor — Screenplay Architecture & Three-Act Scene Beats.");
                if (txtActiveCallTitle != null) txtActiveCallTitle.setText("Kino Script Doctor");
                if (txtActiveCallSubtitle != null) {
                    txtActiveCallSubtitle.setText("Creative Subagent • Screenplay");
                    txtActiveCallSubtitle.setTextColor(Color.parseColor("#38bdf8"));
                }
                break;
            case KINO_CHARACTERS:
                chipCharacters.setBackgroundResource(R.drawable.bg_chip_selected);
                chipCharacters.setTextColor(Color.parseColor("#fbbf24"));
                txtSessionHint.setText("Subagent: Kino Character Studio — Psychology, Want vs Need, and Dialogue.");
                if (txtActiveCallTitle != null) txtActiveCallTitle.setText("Kino Character Studio");
                if (txtActiveCallSubtitle != null) {
                    txtActiveCallSubtitle.setText("Creative Subagent • Characters");
                    txtActiveCallSubtitle.setTextColor(Color.parseColor("#a855f7"));
                }
                break;
            case KINO_SHOTLIST:
                chipShotlist.setBackgroundResource(R.drawable.bg_chip_selected);
                chipShotlist.setTextColor(Color.parseColor("#fbbf24"));
                txtSessionHint.setText("Subagent: Kino Shotlist Creator — Cinematography, Camera Movement & Mood.");
                if (txtActiveCallTitle != null) txtActiveCallTitle.setText("Kino Shotlist Creator");
                if (txtActiveCallSubtitle != null) {
                    txtActiveCallSubtitle.setText("Creative Subagent • Cinematography");
                    txtActiveCallSubtitle.setTextColor(Color.parseColor("#ec4899"));
                }
                break;
        }
    }

    private void showVoiceSelectionDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this, android.R.style.Theme_DeviceDefault_Dialog_Alert);
        builder.setTitle("Select Milo Voice Engine");
        builder.setSingleChoiceItems(VOICE_DISPLAY_NAMES, selectedVoiceIndex, (dialog, which) -> {
            selectedVoiceIndex = which;
            txtCurrentVoiceName.setText(VOICE_DISPLAY_NAMES[which]);
            dialog.dismiss();
            Toast.makeText(this, "Voice: " + VOICE_DISPLAY_NAMES[which], Toast.LENGTH_SHORT).show();
        });
        builder.setNegativeButton("Cancel", null);
        builder.show();
    }

    private String getSelectedVoiceKey() {
        return VOICE_KEYS[selectedVoiceIndex];
    }

    private void checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{
                    Manifest.permission.RECORD_AUDIO,
                    Manifest.permission.MODIFY_AUDIO_SETTINGS
                }, PERMISSION_REQ_CODE);
            }
        }
    }

    // =========================================================================
    // CALL LIFECYCLE & STATE SWITCHING
    // =========================================================================
    private void startCallSession() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M &&
            checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            checkPermissions();
            return;
        }

        layoutStandby.setVisibility(View.GONE);
        layoutIncoming.setVisibility(View.GONE);
        layoutActive.setVisibility(View.VISIBLE);

        isCallActive = true;
        isMuted = false;
        callSeconds = 0;
        startCallTimer();

        pulsingOrb.setState(PulsingOrbView.State.LISTENING);
        audioEngine.startContinuousListening();

        // Milo Tailored Greeting based on Mode
        String selectedVoice = getSelectedVoiceKey();
        boolean isTamil = selectedVoice.startsWith("ta-");
        String greeting = "";

        switch (currentMode) {
            case MILO_MAIN:
                greeting = isTamil
                    ? "வணக்கம் ஜெஃப்பி! நான் உங்க மிலோ பேசுறேன். சொல்லுங்க, இன்னைக்கு என்ன பண்ணலாம்?"
                    : "Hey Jeffy! Milo here. What's on your mind today?";
                break;
            case KINO_STORY:
                greeting = isTamil
                    ? "வணக்கம் ஜெஃப்பி! மிலோவோட சப்-ஏஜென்ட் கினோ ஸ்கிரிப்ட் டாக்டர் லைன்ல இருக்கேன். நம்ம கதையோட எந்த Scene beat பத்தி பேசலாம்?"
                    : "Hey Jeffy! Subagent Kino Script Doctor is active. Which screenplay beat or plot twist are we developing?";
                break;
            case KINO_CHARACTERS:
                greeting = isTamil
                    ? "வணக்கம் ஜெஃப்பி! கினோ கேரக்டர் ஸ்டுடியோ லைன்ல இருக்கேன். எந்த கேரக்டர் ஆர்க் பத்தி பேச போறோம்?"
                    : "Ready Jeffy! Subagent Kino Character Studio is active. Let's explore your character psychology.";
                break;
            case KINO_SHOTLIST:
                greeting = isTamil
                    ? "வணக்கம் டைரக்டர் ஜெஃப்பி! கினோ ஷாட்லிஸ்ட் ஏஜென்ட் லைன்ல இருக்கேன். அடுத்த சீனுக்கான கேமரா ஆங்கிள்ஸ் மற்றும் லைட்டிங் ப்ளான் பண்ணலாமா?"
                    : "Director Jeffy, Subagent Kino Shotlist Creator here. Let's frame your visual scene.";
                break;
        }

        String speakerName = (currentMode == CompanionMode.MILO_MAIN) ? "Milo" : "Kino";
        txtSpeechBubble.setText(speakerName + ": " + greeting);
        String ttsUrl = networkClient.getTtsUrl(greeting, selectedVoice);
        audioEngine.playAudioUrl(ttsUrl);
    }

    private void triggerIncomingRing(String reason) {
        layoutStandby.setVisibility(View.GONE);
        layoutActive.setVisibility(View.GONE);
        layoutIncoming.setVisibility(View.VISIBLE);

        TextView txtReason = findViewById(R.id.txtIncomingReason);
        if (txtReason != null) txtReason.setText(reason);

        // Native Ringtone
        try {
            Uri alert = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_RINGTONE);
            if (alert == null) alert = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
            ringtone = RingtoneManager.getRingtone(getApplicationContext(), alert);
            if (ringtone != null) ringtone.play();
        } catch (Exception ignored) {}

        // Native Vibration Pattern
        if (vibrator != null) {
            long[] pattern = {0, 400, 300, 400, 1000};
            vibrator.vibrate(pattern, 0);
        }
    }

    private void stopRing() {
        if (ringtone != null && ringtone.isPlaying()) {
            ringtone.stop();
        }
        if (vibrator != null) {
            vibrator.cancel();
        }
    }

    private void acceptCallSession() {
        stopRing();
        startCallSession();
    }

    private void declineCallSession() {
        stopRing();
        layoutIncoming.setVisibility(View.GONE);
        layoutActive.setVisibility(View.GONE);
        layoutStandby.setVisibility(View.VISIBLE);
    }

    private void endCallSession() {
        isCallActive = false;
        stopCallTimer();
        audioEngine.stopListening();

        layoutActive.setVisibility(View.GONE);
        layoutIncoming.setVisibility(View.GONE);
        layoutStandby.setVisibility(View.VISIBLE);
    }

    private void toggleMute() {
        isMuted = !isMuted;
        audioEngine.setMuted(isMuted);
        waveformVisualizer.setMuted(isMuted);
        txtMuteIcon.setText(isMuted ? "🔇" : "🎙️");
        Toast.makeText(this, isMuted ? "Microphone Muted" : "Microphone Active", Toast.LENGTH_SHORT).show();
    }

    private void toggleSpeaker() {
        audioEngine.toggleSpeakerphone();
        txtSpeakerIcon.setText(audioEngine.isSpeakerphoneOn() ? "🔊" : "🔈");
    }

    private void startCallTimer() {
        callSeconds = 0;
        timerHandler.removeCallbacksAndMessages(null);
        timerHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (isCallActive) {
                    callSeconds++;
                    int mins = callSeconds / 60;
                    int secs = callSeconds % 60;
                    txtCallTimer.setText(String.format(Locale.US, "%02d:%02d", mins, secs));
                    timerHandler.postDelayed(this, 1000);
                }
            }
        }, 1000);
    }

    private void stopCallTimer() {
        timerHandler.removeCallbacksAndMessages(null);
    }

    // =========================================================================
    // AUDIO ENGINE LISTENER CALLBACKS
    // =========================================================================
    @Override
    public void onAmplitudeUpdate(float normalizedAmp) {
        if (waveformVisualizer != null && isCallActive) {
            waveformVisualizer.updateAmplitude(normalizedAmp);
        }
    }

    @Override
    public void onSpeechRecorded(byte[] wavBytes) {
        if (!isCallActive) return;
        handleRecordedSpeech(wavBytes);
    }

    private void handleRecordedSpeech(byte[] wavBytes) {
        final String speakerName = (currentMode == CompanionMode.MILO_MAIN) ? "Milo" : "Kino";
        pulsingOrb.setState(PulsingOrbView.State.THINKING);
        txtSpeechBubble.setText("Transcribing speech with Gemini...");

        networkClient.transcribeAudio(wavBytes, new NetworkClient.TranscribeCallback() {
            @Override
            public void onSuccess(String transcript) {
                if (transcript.isEmpty()) {
                    pulsingOrb.setState(PulsingOrbView.State.LISTENING);
                    txtSpeechBubble.setText("Ready to brainstorm, Jeffy. Speak freely!");
                    return;
                }

                txtSpeechBubble.setText("You: " + transcript + "\n\n" + speakerName + " is thinking...");
                String voice = getSelectedVoiceKey();
                String modeName = currentMode.name().toLowerCase();

                networkClient.queryMilo(transcript, voice, modeName, new NetworkClient.QueryCallback() {
                    @Override
                    public void onSuccess(String reply, String cleanSpeech) {
                        txtSpeechBubble.setText("You: " + transcript + "\n\n" + speakerName + ": " + reply);
                        String ttsUrl = networkClient.getTtsUrl(cleanSpeech, voice);
                        audioEngine.playAudioUrl(ttsUrl);
                    }

                    @Override
                    public void onError(String error) {
                        pulsingOrb.setState(PulsingOrbView.State.LISTENING);
                        txtSpeechBubble.setText("Query error: " + error);
                    }
                });
            }

            @Override
            public void onError(String error) {
                pulsingOrb.setState(PulsingOrbView.State.LISTENING);
                txtSpeechBubble.setText("Transcription failed: " + error);
            }
        });
    }

    @Override
    public void onPlaybackStarted() {
        if (pulsingOrb != null) pulsingOrb.setState(PulsingOrbView.State.SPEAKING);
        if (waveformVisualizer != null) waveformVisualizer.setSpeaking(true);
    }

    @Override
    public void onPlaybackFinished() {
        if (pulsingOrb != null) pulsingOrb.setState(PulsingOrbView.State.LISTENING);
        if (waveformVisualizer != null) waveformVisualizer.setSpeaking(false);
    }

    @Override
    public void onBackPressed() {
        if (isCallActive) {
            endCallSession();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        stopRing();
        stopCallTimer();
        if (audioEngine != null) audioEngine.stopListening();
        super.onDestroy();
    }
}
