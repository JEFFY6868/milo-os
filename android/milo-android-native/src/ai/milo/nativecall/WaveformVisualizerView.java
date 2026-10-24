package ai.milo.nativecall;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.view.View;

/**
 * Premium 2D Hardware-Accelerated Neon Audio Visualizer.
 * Renders 10 symmetric vertical bars with golden gradient fills, dynamic glow,
 * and fluid spring interpolation driven by real native AudioRecord PCM stream.
 */
public class WaveformVisualizerView extends View {
    private Paint barPaint;
    private Paint glowPaint;
    private static final int NUM_BARS = 10;
    private float[] currentHeights = new float[NUM_BARS];
    private float[] targetHeights = new float[NUM_BARS];
    private boolean isMuted = false;
    private boolean isSpeaking = false;

    public WaveformVisualizerView(Context context) {
        super(context);
        init();
    }

    public WaveformVisualizerView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        barPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        barPaint.setStyle(Paint.Style.FILL);

        glowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        glowPaint.setStyle(Paint.Style.FILL);
        glowPaint.setColor(Color.parseColor("#33f59e0b"));

        for (int i = 0; i < NUM_BARS; i++) {
            currentHeights[i] = 12f;
            targetHeights[i] = 12f;
        }
    }

    public void updateAmplitude(float normalizedAmp) {
        if (isMuted) {
            for (int i = 0; i < NUM_BARS; i++) targetHeights[i] = 8f;
            postInvalidateOnAnimation();
            return;
        }

        for (int i = 0; i < NUM_BARS; i++) {
            // Symmetrical frequency bell curve (center bars bounce higher)
            float distFromCenter = Math.abs(i - (NUM_BARS - 1) / 2f) / ((NUM_BARS - 1) / 2f);
            float bellWeight = 1.0f - (distFromCenter * 0.45f);

            float jitter = (float) (Math.random() * 12f * normalizedAmp);
            float h = 12f + (normalizedAmp * 85f * bellWeight) + jitter;
            targetHeights[i] = Math.max(12f, Math.min(110f, h));
        }
        postInvalidateOnAnimation();
    }

    public void setMuted(boolean muted) {
        this.isMuted = muted;
        postInvalidateOnAnimation();
    }

    public void setSpeaking(boolean speaking) {
        this.isSpeaking = speaking;
        postInvalidateOnAnimation();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        int width = getWidth();
        int height = getHeight();
        if (width == 0 || height == 0) return;

        float barWidth = 10f;
        float spacing = 12f;
        float totalWidth = (NUM_BARS * barWidth) + ((NUM_BARS - 1) * spacing);
        float startX = (width - totalWidth) / 2f;
        float centerY = height / 2f;

        // Apply Gold Linear Gradient
        LinearGradient grad = new LinearGradient(
            0, centerY - 50, 0, centerY + 50,
            Color.parseColor("#fde047"), // Light gold
            Color.parseColor("#d97706"), // Deep amber
            Shader.TileMode.CLAMP
        );
        barPaint.setShader(grad);

        boolean needsNextFrame = false;

        for (int i = 0; i < NUM_BARS; i++) {
            if (isSpeaking) {
                // Harmonic fluid wave while Milo is speaking
                float wave = (float) Math.sin(System.currentTimeMillis() / 140.0 + i * 0.7);
                currentHeights[i] = 24f + (wave * 22f);
                needsNextFrame = true;
            } else {
                currentHeights[i] += (targetHeights[i] - currentHeights[i]) * 0.35f;
                targetHeights[i] = Math.max(12f, targetHeights[i] * 0.82f);
                if (Math.abs(targetHeights[i] - currentHeights[i]) > 0.4f) {
                    needsNextFrame = true;
                }
            }

            float halfH = currentHeights[i] / 2f;
            float left = startX + (i * (barWidth + spacing));
            float right = left + barWidth;
            float top = centerY - halfH;
            float bottom = centerY + halfH;

            // Outer soft glow
            canvas.drawRoundRect(left - 2, top - 2, right + 2, bottom + 2, (barWidth + 4) / 2f, (barWidth + 4) / 2f, glowPaint);

            // Core Bar
            canvas.drawRoundRect(left, top, right, bottom, barWidth / 2f, barWidth / 2f, barPaint);
        }

        if (needsNextFrame) {
            postInvalidateOnAnimation();
        }
    }
}
