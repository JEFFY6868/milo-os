package ai.milo.nativecall;

import android.content.Context;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.MediaPlayer;
import android.media.MediaRecorder;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

/**
 * Pure Native Android Audio Engine.
 * Direct AudioRecord PCM recording with hardware level volume estimation,
 * in-memory WAV encoder, Voice Activity Detection, and MediaPlayer streaming.
 */
public class AudioEngine {
    private static final String TAG = "MiloAudioEngine";
    private static final int SAMPLE_RATE = 16000;
    private static final int CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO;
    private static final int AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT;

    public interface AudioListener {
        void onAmplitudeUpdate(float normalizedAmp);
        void onSpeechRecorded(byte[] wavBytes);
        void onPlaybackStarted();
        void onPlaybackFinished();
    }

    private final Context context;
    private final AudioListener listener;
    private final Handler mainHandler;

    private AudioRecord audioRecord;
    private Thread recordingThread;
    private boolean isRecording = false;
    private boolean isMuted = false;
    private boolean isSpeakerphoneOn = true;

    // Buffer for speech accumulation
    private final ByteArrayOutputStream speechBuffer = new ByteArrayOutputStream();
    private boolean isCapturingSpeech = false;
    private long lastVoiceDetectedTime = 0;
    private static final long SILENCE_THRESHOLD_MS = 1200;
    private static final float VOICE_ENERGY_THRESHOLD = 0.15f;

    private MediaPlayer mediaPlayer;

    public AudioEngine(Context context, AudioListener listener) {
        this.context = context;
        this.listener = listener;
        this.mainHandler = new Handler(Looper.getMainLooper());
    }

    public synchronized void startContinuousListening() {
        if (isRecording) return;

        int bufferSize = Math.max(
            AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT),
            SAMPLE_RATE * 2 // 1 second buffer
        );

        try {
            audioRecord = new AudioRecord(
                MediaRecorder.AudioSource.VOICE_COMMUNICATION,
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSize
            );

            if (audioRecord.getState() != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "AudioRecord initialization failed.");
                return;
            }

            audioRecord.startRecording();
            isRecording = true;

            recordingThread = new Thread(this::recordLoop, "MiloAudioRecordThread");
            recordingThread.start();
            Log.i(TAG, "Native AudioRecord started at " + SAMPLE_RATE + "Hz");
        } catch (SecurityException se) {
            Log.e(TAG, "Missing RECORD_AUDIO permission: " + se.getMessage());
        } catch (Exception e) {
            Log.e(TAG, "Error starting AudioRecord: " + e.getMessage());
        }
    }

    public synchronized void stopListening() {
        isRecording = false;
        if (audioRecord != null) {
            try {
                audioRecord.stop();
                audioRecord.release();
            } catch (Exception ignored) {}
            audioRecord = null;
        }

        if (recordingThread != null) {
            try {
                recordingThread.join(500);
            } catch (InterruptedException ignored) {}
            recordingThread = null;
        }

        stopPlayback();
    }

    private void recordLoop() {
        short[] buffer = new short[512];

        while (isRecording) {
            if (isMuted) {
                try { Thread.sleep(50); } catch (InterruptedException ignored) {}
                continue;
            }

            int read = audioRecord.read(buffer, 0, buffer.length);
            if (read > 0) {
                // Calculate RMS energy
                long sum = 0;
                for (int i = 0; i < read; i++) {
                    sum += buffer[i] * buffer[i];
                }
                double rms = Math.sqrt((double) sum / read);
                float normalized = (float) Math.min(1.0, rms / 18000.0);

                mainHandler.post(() -> {
                    if (listener != null) listener.onAmplitudeUpdate(normalized);
                });

                // Auto-VAD Voice detection
                long now = System.currentTimeMillis();
                if (normalized > VOICE_ENERGY_THRESHOLD) {
                    lastVoiceDetectedTime = now;
                    if (!isCapturingSpeech) {
                        isCapturingSpeech = true;
                        speechBuffer.reset();
                    }
                }

                if (isCapturingSpeech) {
                    // Append PCM bytes
                    byte[] byteBuf = new byte[read * 2];
                    for (int i = 0; i < read; i++) {
                        byteBuf[i * 2] = (byte) (buffer[i] & 0xFF);
                        byteBuf[i * 2 + 1] = (byte) ((buffer[i] >> 8) & 0xFF);
                    }
                    speechBuffer.write(byteBuf, 0, byteBuf.length);

                    // Silence detection
                    if (now - lastVoiceDetectedTime > SILENCE_THRESHOLD_MS && speechBuffer.size() > SAMPLE_RATE) {
                        isCapturingSpeech = false;
                        byte[] pcmData = speechBuffer.toByteArray();
                        speechBuffer.reset();
                        byte[] wav = createWavFile(pcmData, SAMPLE_RATE, 1, 16);

                        mainHandler.post(() -> {
                            if (listener != null) listener.onSpeechRecorded(wav);
                        });
                    }
                }
            }
        }
    }

    // Manual Push-To-Talk
    public synchronized void startManualSpeechCapture() {
        isCapturingSpeech = true;
        speechBuffer.reset();
    }

    public synchronized byte[] stopManualSpeechCapture() {
        isCapturingSpeech = false;
        byte[] pcmData = speechBuffer.toByteArray();
        speechBuffer.reset();
        if (pcmData.length < 1000) return null;
        return createWavFile(pcmData, SAMPLE_RATE, 1, 16);
    }

    public void setMuted(boolean muted) {
        this.isMuted = muted;
    }

    public void toggleSpeakerphone() {
        AudioManager am = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
        if (am != null) {
            isSpeakerphoneOn = !isSpeakerphoneOn;
            am.setSpeakerphoneOn(isSpeakerphoneOn);
        }
    }

    public boolean isSpeakerphoneOn() {
        return isSpeakerphoneOn;
    }

    public void playAudioUrl(String url) {
        stopPlayback();
        try {
            mediaPlayer = new MediaPlayer();
            mediaPlayer.setAudioStreamType(AudioManager.STREAM_VOICE_CALL);
            mediaPlayer.setDataSource(url);
            mediaPlayer.setOnPreparedListener(mp -> {
                mp.start();
                mainHandler.post(() -> {
                    if (listener != null) listener.onPlaybackStarted();
                });
            });
            mediaPlayer.setOnCompletionListener(mp -> {
                mainHandler.post(() -> {
                    if (listener != null) listener.onPlaybackFinished();
                });
            });
            mediaPlayer.setOnErrorListener((mp, what, extra) -> {
                Log.w(TAG, "MediaPlayer error: " + what);
                mainHandler.post(() -> {
                    if (listener != null) listener.onPlaybackFinished();
                });
                return true;
            });
            mediaPlayer.prepareAsync();
        } catch (IOException e) {
            Log.e(TAG, "Error playing audio: " + e.getMessage());
        }
    }

    public void stopPlayback() {
        if (mediaPlayer != null) {
            try {
                if (mediaPlayer.isPlaying()) mediaPlayer.stop();
                mediaPlayer.release();
            } catch (Exception ignored) {}
            mediaPlayer = null;
        }
    }

    /**
     * Converts raw PCM bytes into a standard RIFF/WAV byte array.
     */
    public static byte[] createWavFile(byte[] pcmData, int sampleRate, int channels, int bitsPerSample) {
        int totalDataLen = pcmData.length + 36;
        int byteRate = sampleRate * channels * bitsPerSample / 8;

        byte[] header = new byte[44];
        header[0] = 'R'; header[1] = 'I'; header[2] = 'F'; header[3] = 'F';
        header[4] = (byte) (totalDataLen & 0xff);
        header[5] = (byte) ((totalDataLen >> 8) & 0xff);
        header[6] = (byte) ((totalDataLen >> 16) & 0xff);
        header[7] = (byte) ((totalDataLen >> 24) & 0xff);
        header[8] = 'W'; header[9] = 'A'; header[10] = 'V'; header[11] = 'E';
        header[12] = 'f'; header[13] = 'm'; header[14] = 't'; header[15] = ' ';
        header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0; // subchunk1size (16 for PCM)
        header[20] = 1; header[21] = 0; // audio format (1 = PCM)
        header[22] = (byte) channels; header[23] = 0;
        header[24] = (byte) (sampleRate & 0xff);
        header[25] = (byte) ((sampleRate >> 8) & 0xff);
        header[26] = (byte) ((sampleRate >> 16) & 0xff);
        header[27] = (byte) ((sampleRate >> 24) & 0xff);
        header[28] = (byte) (byteRate & 0xff);
        header[29] = (byte) ((byteRate >> 8) & 0xff);
        header[30] = (byte) ((byteRate >> 16) & 0xff);
        header[31] = (byte) ((byteRate >> 24) & 0xff);
        header[32] = (byte) (channels * bitsPerSample / 8); header[33] = 0; // block align
        header[34] = (byte) bitsPerSample; header[35] = 0;
        header[36] = 'd'; header[37] = 'a'; header[38] = 't'; header[39] = 'a';
        header[40] = (byte) (pcmData.length & 0xff);
        header[41] = (byte) ((pcmData.length >> 8) & 0xff);
        header[42] = (byte) ((pcmData.length >> 16) & 0xff);
        header[43] = (byte) ((pcmData.length >> 24) & 0xff);

        byte[] out = new byte[header.length + pcmData.length];
        System.arraycopy(header, 0, out, 0, header.length);
        System.arraycopy(pcmData, 0, out, header.length, pcmData.length);
        return out;
    }
}
