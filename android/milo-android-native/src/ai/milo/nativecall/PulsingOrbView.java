package ai.milo.nativecall;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.view.View;

/**
 * Cinematic Luxury Ambient AI Orb.
 * Renders dual out-of-phase breathing rings, deep radial gradients,
 * and illuminated state typography for Milo Voice Engine.
 */
public class PulsingOrbView extends View {
    public enum State {
        IDLE, LISTENING, RECORDING, THINKING, SPEAKING
    }

    private State currentState = State.IDLE;
    private Paint corePaint;
    private Paint borderPaint;
    private Paint ring1Paint;
    private Paint ring2Paint;
    private Paint textPaint;
    private Paint micPaint;

    public PulsingOrbView(Context context) {
        super(context);
        init();
    }

    public PulsingOrbView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        corePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        corePaint.setStyle(Paint.Style.FILL);

        borderPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(3f);

        ring1Paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        ring1Paint.setStyle(Paint.Style.STROKE);
        ring1Paint.setStrokeWidth(2.5f);

        ring2Paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        ring2Paint.setStyle(Paint.Style.STROKE);
        ring2Paint.setStrokeWidth(2f);

        textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        textPaint.setTextAlign(Paint.Align.CENTER);
        textPaint.setFakeBoldText(true);
        textPaint.setTextSize(24f);
        textPaint.setLetterSpacing(0.12f);

        micPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        micPaint.setStyle(Paint.Style.STROKE);
        micPaint.setStrokeWidth(5f);
        micPaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setState(State state) {
        this.currentState = state;
        postInvalidateOnAnimation();
    }

    public State getState() {
        return currentState;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        int cx = getWidth() / 2;
        int cy = getHeight() / 2;
        float coreRadius = Math.min(cx, cy) * 0.62f;

        int primaryColor = Color.parseColor("#f59e0b"); // Luxury Gold/Amber
        String statusLabel = "LISTENING";

        if (currentState == State.RECORDING) {
            primaryColor = Color.parseColor("#f43f5e"); // Crimson
            statusLabel = "RECORDING";
        } else if (currentState == State.SPEAKING) {
            primaryColor = Color.parseColor("#fbbf24"); // Bright Gold
            statusLabel = "SPEAKING";
        } else if (currentState == State.THINKING) {
            primaryColor = Color.parseColor("#38bdf8"); // Sky
            statusLabel = "THINKING";
        } else if (currentState == State.IDLE) {
            primaryColor = Color.parseColor("#64748b");
            statusLabel = "STANDBY";
        }

        long time = System.currentTimeMillis();

        // Dual Out-Of-Phase Pulsing Rings
        float p1 = (time % 2200) / 2200f;
        float r1 = coreRadius + (p1 * coreRadius * 0.5f);
        int a1 = (int) ((1f - p1) * 140);
        ring1Paint.setColor(primaryColor);
        ring1Paint.setAlpha(Math.max(0, a1));
        canvas.drawCircle(cx, cy, r1, ring1Paint);

        float p2 = ((time + 1100) % 2200) / 2200f;
        float r2 = coreRadius + (p2 * coreRadius * 0.5f);
        int a2 = (int) ((1f - p2) * 140);
        ring2Paint.setColor(primaryColor);
        ring2Paint.setAlpha(Math.max(0, a2));
        canvas.drawCircle(cx, cy, r2, ring2Paint);

        // Core Radial Gradient
        RadialGradient grad = new RadialGradient(
            cx, cy - 10, coreRadius,
            new int[]{Color.parseColor("#172033"), Color.parseColor("#070b14")},
            new float[]{0.25f, 1.0f},
            Shader.TileMode.CLAMP
        );
        corePaint.setShader(grad);
        canvas.drawCircle(cx, cy, coreRadius, corePaint);

        // Core Rim
        borderPaint.setColor(primaryColor);
        canvas.drawCircle(cx, cy, coreRadius, borderPaint);

        // Microphones Icon
        micPaint.setColor(primaryColor);
        float micTop = cy - 36f;
        float micBottom = cy + 10f;
        float micHalfW = 14f;

        canvas.drawRoundRect(cx - micHalfW, micTop, cx + micHalfW, micBottom, micHalfW, micHalfW, micPaint);
        canvas.drawArc(cx - micHalfW - 7f, cy - 8f, cx + micHalfW + 7f, cy + 20f, 0, 180, false, micPaint);
        canvas.drawLine(cx, cy + 20f, cx, cy + 34f, micPaint);
        canvas.drawLine(cx - 16f, cy + 34f, cx + 16f, cy + 34f, micPaint);

        // State Text Label
        textPaint.setColor(Color.parseColor("#e2e8f0"));
        canvas.drawText(statusLabel, cx, cy + 68f, textPaint);

        postInvalidateOnAnimation();
    }
}
