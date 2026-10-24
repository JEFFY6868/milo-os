package ai.milo.nativecall;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;

/**
 * Pure Native Android Network Client.
 * Connects directly to Milo Core Server via Tailscale / MagicDNS for speech transcription,
 * reasoning queries, and incoming call push notifications.
 */
public class NetworkClient {
    private static final String TAG = "MiloNetworkClient";
    public static final String DEFAULT_HOST = "http://100.79.103.98:3140";
    public static final String MAGIC_DNS_HOST = "http://milo-1.tail7dfc60.ts.net:3140";

    private String baseHost = DEFAULT_HOST;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    public interface TranscribeCallback {
        void onSuccess(String transcript);
        void onError(String error);
    }

    public interface QueryCallback {
        void onSuccess(String reply, String cleanSpeech);
        void onError(String error);
    }

    public void setHost(String host) {
        this.baseHost = host;
    }

    public String getBaseHost() {
        return baseHost;
    }

    public void transcribeAudio(byte[] wavBytes, TranscribeCallback callback) {
        new Thread(() -> {
            try {
                String boundary = "===MiloBoundary" + System.currentTimeMillis() + "===";
                URL url = new URL(baseHost + "/api/voice/transcribe");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setConnectTimeout(12000);
                conn.setReadTimeout(35000);
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);

                DataOutputStream dos = new DataOutputStream(conn.getOutputStream());
                dos.writeBytes("--" + boundary + "\r\n");
                dos.writeBytes("Content-Disposition: form-data; name=\"audio\"; filename=\"recording.wav\"\r\n");
                dos.writeBytes("Content-Type: audio/wav\r\n\r\n");
                dos.write(wavBytes);
                dos.writeBytes("\r\n--" + boundary + "--\r\n");
                dos.flush();
                dos.close();

                int code = conn.getResponseCode();
                InputStream is = (code >= 200 && code < 300) ? conn.getInputStream() : conn.getErrorStream();
                String resp = readStream(is);
                conn.disconnect();

                JSONObject json = new JSONObject(resp);
                if (json.optBoolean("success", false) || json.has("text")) {
                    String text = json.optString("text", "").trim();
                    mainHandler.post(() -> callback.onSuccess(text));
                } else {
                    mainHandler.post(() -> callback.onError("Transcription empty: " + resp));
                }
            } catch (Exception e) {
                Log.e(TAG, "Transcribe error: " + e.getMessage());
                mainHandler.post(() -> callback.onError(e.getMessage()));
            }
        }).start();
    }

    public void queryMilo(String query, String voice, QueryCallback callback) {
        queryMilo(query, voice, "milo_main", callback);
    }

    public void queryMilo(String query, String voice, String mode, QueryCallback callback) {
        new Thread(() -> {
            try {
                URL url = new URL(baseHost + "/api/voice/query");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setConnectTimeout(12000);
                conn.setReadTimeout(35000);
                conn.setRequestProperty("Content-Type", "application/json");

                JSONObject body = new JSONObject();
                body.put("query", query);
                body.put("voice", voice);
                body.put("mode", mode);

                DataOutputStream dos = new DataOutputStream(conn.getOutputStream());
                dos.write(body.toString().getBytes("UTF-8"));
                dos.flush();
                dos.close();

                int code = conn.getResponseCode();
                InputStream is = (code >= 200 && code < 300) ? conn.getInputStream() : conn.getErrorStream();
                String resp = readStream(is);
                conn.disconnect();

                JSONObject json = new JSONObject(resp);
                String reply = json.optString("reply", "");
                String cleanSpeech = json.optString("clean_speech", reply);

                mainHandler.post(() -> callback.onSuccess(reply, cleanSpeech));
            } catch (Exception e) {
                Log.e(TAG, "Query error: " + e.getMessage());
                mainHandler.post(() -> callback.onError(e.getMessage()));
            }
        }).start();
    }

    public String getTtsUrl(String text, String voice) {
        try {
            return baseHost + "/api/voice/tts?text=" + URLEncoder.encode(text, "UTF-8")
                    + "&voice=" + URLEncoder.encode(voice, "UTF-8")
                    + "&format=opus";
        } catch (Exception e) {
            return baseHost + "/api/voice/tts";
        }
    }

    private static String readStream(InputStream is) throws Exception {
        if (is == null) return "";
        BufferedReader br = new BufferedReader(new InputStreamReader(is, "UTF-8"));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) {
            sb.append(line);
        }
        return sb.toString();
    }
}
