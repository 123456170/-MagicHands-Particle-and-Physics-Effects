import json

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="MagicHands: Particle and Physics Effects",
    page_icon="🪄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🪄 MagicHands: Particle and Physics Effects")
st.caption(
    "Fully local Streamlit demo. It starts immediately with realistic synthetic hand data, "
    "generates a browser-local demo video, and can optionally use your webcam through "
    "browser-side MediaPipe Tasks. No API key, no upload."
)

if "delete_nonce" not in st.session_state:
    st.session_state["delete_nonce"] = 0

with st.sidebar:
    st.header("Run controls")

    input_mode = st.radio(
        "Input source",
        ["Automatic synthetic demo", "Try webcam (local)"],
        index=0,
        help="Synthetic demo always works. Webcam uses local browser tracking if permitted.",
    )

    quality = st.slider("Quality", 1, 5, 3, help="Higher quality allows more particles.")
    sound = st.checkbox("Enable sound", True, help="Web Audio remains capped below the max volume setting.")
    auto_video = st.checkbox("Auto-generate local demo video", True)
    show_landmarks = st.checkbox("Show hand landmarks", True)

    st.markdown("---")
    st.subheader("Effects")

    aura = st.checkbox("Aura", True, help="Particles emitted from fingertips.")
    orb = st.checkbox("Orb", True, help="Pinch spawns and grows an orb.")
    throw = st.checkbox("Throw", True, help="Armed fast release launches the orb.")
    lightning = st.checkbox("Lightning", True, help="Arc between two armed nearby hands.")
    trails = st.checkbox("Orb trails", True, help="Thrown orbs leave particle trails.")
    bursts = st.checkbox("Bounce/expiry bursts", True, help="Small particle explosions on impact or expiry.")

    st.markdown("---")
    st.subheader("Advanced tuning")

    with st.expander("Gesture and physics thresholds"):
        pinch_start = st.slider("Pinch start ratio", 0.10, 0.45, 0.30, 0.01)
        pinch_end = st.slider("Pinch end ratio", 0.35, 0.70, 0.42, 0.01)
        arm_hold_ms = st.slider("Arm hold ms", 300, 2500, 1000, 50)
        refractory_ms = st.slider("Refractory ms", 100, 1500, 450, 25)
        throw_window_ms = st.slider("Velocity window ms", 50, 250, 100, 10)
        throw_gain = st.slider("Throw gain", 0.5, 3.0, 1.35, 0.05)
        throw_min_speed = st.slider("Throw min speed px/s", 80, 900, 260, 10)
        throw_max_speed = st.slider("Throw max speed px/s", 500, 3500, 1800, 50)
        gravity = st.slider("Gravity px/s²", 0, 2500, 950, 25)
        damping = st.slider("Particle damping", 0.900, 0.999, 0.985, 0.001)
        bounce = st.slider("Wall bounce", 0.00, 0.95, 0.55, 0.01)
        lightning_dist = st.slider("Lightning max palm distance", 1.0, 4.0, 1.9, 0.1)
        max_volume = st.slider("Max volume cap", 0.00, 0.20, 0.18, 0.01)

    st.markdown("---")

    if st.button("Delete all local demo data", use_container_width=True):
        st.session_state["delete_nonce"] += 1

    delete_nonce = int(st.session_state["delete_nonce"])

    if delete_nonce:
        st.info("Delete requested. The embedded page will clear local blobs, stop camera access if present, and reset the simulation.")

    st.markdown("---")
    st.subheader("Privacy")
    st.markdown(
        """
        - Video and audio processing stay in your browser.
        - No network upload of camera frames.
        - No API key required.
        - Camera turns on only when you press **Enable camera** inside the app.
        - Generated demo video is a local browser blob unless you download it.
        - **Delete all local demo data** clears generated blobs and resets local storage used by the embedded page.
        """
    )

    st.subheader("Licenses")
    st.markdown(
        """
        - Streamlit: Apache-2.0.
        - MediaPipe Tasks Vision, when loaded by the browser: Apache-2.0.
        - MediaPipe hand/gesture models, when loaded by the browser: Apache-2.0.
        - Embedded JavaScript uses standard browser APIs.
        - No paid library, model, asset, or API is used.
        """
    )

    st.subheader("Known limits")
    st.markdown(
        """
        - Browser camera permission may be blocked in some embedded frames.
        - MediaPipe model download needs internet; offline mode uses the synthetic demo.
        - Canvas 2D is used with typed arrays, not a full WebGL shader particle system.
        - Auto-generated demo video is synthetic canvas video; real camera recording is manual.
        - Gesture accuracy depends on lighting, camera angle, occlusion, and distance.
        - Audio may stay silent until you click the canvas because browsers block autoplay.
        """
    )


PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MagicHands Embedded Demo</title>
  <style>
    :root {
      color-scheme: dark;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: #030712;
      color: #e5e7eb;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    }

    #mh-root {
      padding: 10px;
      min-height: 100vh;
    }

    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-bottom: 6px;
    }

    .chip {
      border: 1px solid #334155;
      background: #0f172a;
      color: #cbd5e1;
      padding: 7px 10px;
      border-radius: 999px;
      cursor: pointer;
      font-size: 13px;
      user-select: none;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      transition: border-color 120ms ease, background 120ms ease, color 120ms ease;
    }

    .chip:hover {
      border-color: #60a5fa;
      color: #fff;
    }

    .chip.on {
      background: #1d4ed8;
      border-color: #60a5fa;
      color: #fff;
    }

    .chip.off {
      opacity: 0.72;
    }

    .chip input[type="range"] {
      width: 110px;
      accent-color: #60a5fa;
    }

    .status {
      font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      color: #94a3b8;
      margin: 4px 0 8px;
      min-height: 16px;
    }

    .stage {
      position: relative;
      width: 100%;
      max-width: 980px;
      aspect-ratio: 16 / 9;
      background: #000;
      border: 1px solid #1f2937;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 18px 60px rgba(0, 0, 0, 0.35);
    }

    canvas {
      width: 100%;
      height: 100%;
      display: block;
      touch-action: none;
    }

    video#cam {
      display: none;
    }

    video#demo-video {
      display: none;
      width: 100%;
      max-width: 980px;
      margin-top: 8px;
      border-radius: 10px;
      background: #000;
      border: 1px solid #1f2937;
    }

    .hud {
      position: absolute;
      left: 10px;
      top: 10px;
      font: 12px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      background: rgba(2, 6, 23, 0.62);
      padding: 8px 10px;
      border-radius: 9px;
      pointer-events: none;
      white-space: pre-wrap;
      max-width: 64%;
      color: #dbeafe;
      border: 1px solid rgba(148, 163, 184, 0.18);
      backdrop-filter: blur(4px);
    }

    .privacy {
      position: absolute;
      right: 10px;
      top: 10px;
      font: 11px/1.3 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      background: rgba(2, 6, 23, 0.66);
      padding: 7px 9px;
      border-radius: 9px;
      color: #86efac;
      pointer-events: none;
      border: 1px solid rgba(34, 197, 94, 0.22);
      backdrop-filter: blur(4px);
    }

    .event-log {
      width: 100%;
      max-width: 980px;
      min-height: 72px;
      max-height: 110px;
      overflow: auto;
      margin-top: 8px;
      padding: 8px 10px;
      border: 1px solid #1f2937;
      border-radius: 10px;
      background: #020617;
      color: #a5b4fc;
      font: 11px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: pre-wrap;
    }

    .download-row {
      margin-top: 6px;
      font-size: 13px;
    }

    a#download-demo {
      display: none;
      color: #93c5fd;
      text-decoration: none;
      border: 1px solid #334155;
      padding: 7px 10px;
      border-radius: 9px;
      background: #0f172a;
    }

    a#download-demo:hover {
      border-color: #60a5fa;
      color: #fff;
    }

    .legend {
      margin-top: 8px;
      color: #94a3b8;
      font-size: 12px;
      line-height: 1.45;
      max-width: 980px;
    }
  </style>
</head>
<body>
  <div id="mh-root">
    <div class="toolbar">
      <button id="btn-camera" class="chip">Enable camera</button>
      <button id="btn-record" class="chip">Record local demo video</button>
      <button id="btn-delete" class="chip">Delete all data</button>
      <button id="btn-aura" class="chip on">Aura</button>
      <button id="btn-orb" class="chip on">Orb</button>
      <button id="btn-throw" class="chip on">Throw</button>
      <button id="btn-lightning" class="chip on">Lightning</button>
      <button id="btn-trails" class="chip on">Trails</button>
      <button id="btn-bursts" class="chip on">Bursts</button>
      <button id="btn-sound" class="chip on">Sound</button>
      <label class="chip">
        Quality
        <input id="quality" type="range" min="1" max="5" step="1" value="3" />
        <span id="quality-value">3</span>
      </label>
    </div>

    <div id="status" class="status">Starting MagicHands...</div>

    <div class="stage" id="stage">
      <canvas id="mh-canvas" width="960" height="540"></canvas>
      <video id="cam" playsinline muted></video>
      <div id="hud" class="hud">Loading...</div>
      <div id="privacy" class="privacy">Camera OFF • local only • no upload</div>
    </div>

    <div id="event-log" class="event-log">No events yet.</div>

    <video id="demo-video" controls playsinline></video>
    <div class="download-row">
      <a id="download-demo" href="#" download="magichands-demo.webm">Download generated demo video</a>
    </div>

    <div class="legend">
      Demo sequence: open palms arm the hands, left pinch grows an orb, fast left release throws it,
      both hands come close for lightning, then right pinch and throw repeat. Move the mouse over the
      canvas for pointer particles. Click the canvas once to unlock browser audio.
    </div>
  </div>

  <script>
    const DEFAULT_CONFIG = {
      targetFps: 60, // desired frame rate
      minFps: 30, // auto quality drops below this frame rate
      particleCapacity: 6000, // typed-array pool size, avoids per-frame allocation
      maxParticlesByQuality: [700, 1400, 2400, 3600, 5000], // quality 1..5 active cap
      orbCapacity: 16, // reusable orb pool
      quality: 3, // user-selected quality 1..5
      soundEnabled: true, // master sound switch
      maxVolume: 0.18, // hard Web Audio gain cap
      showLandmarks: true, // draw 21-point hand skeleton
      autoDemoVideo: true, // generate a local synthetic demo clip
      demoVideoSeconds: 6, // length of auto clip
      inputMode: "demo", // demo or camera
      deleteNonce: 0, // changing this clears local blobs
      mirrorCamera: true, // mirror front-camera view for natural interaction
      effects: {
        aura: true, // fingertip particle aura
        orb: true, // pinch orb effect
        throw: true, // release throw physics
        lightning: true, // two-hand electric arc
        trails: true, // thrown orb particle trails
        bursts: true // bounce and expiry particle bursts
      },
      thresholds: {
        pinchStart: 0.30, // pinch begins below this thumb-index/palm-width ratio
        pinchEnd: 0.42, // pinch releases above this ratio, hysteresis
        armHoldMs: 1000, // open palm hold time required before risky actions
        armValidMs: 8000, // how long arming remains valid
        refractoryMs: 450, // cooldown so one motion produces one action
        throwWindowMs: 100, // velocity estimation window
        throwGain: 1.35, // scales palm velocity into launch velocity
        throwMinSpeed: 260, // minimum palm speed to treat release as throw
        throwMaxSpeed: 1800, // clamps launch speed in pixels/second
        auraEmitPerFinger: 2, // base particles per fingertip per frame
        auraMaxSpeed: 900, // fingertip speed mapped to color maximum
        lightningMaxPalmDist: 1.9, // normalized two-hand distance for arc
        gravity: 950, // orb downward acceleration px/s^2
        damping: 0.985, // particle drag reference at 60 fps
        bounce: 0.55, // wall restitution
        particleLifeMin: 0.35, // shortest particle lifetime seconds
        particleLifeMax: 1.15, // longest particle lifetime seconds
        trailSpeed: 90, // minimum orb speed for trail particles
        burstMinImpact: 180, // minimum impact speed for bounce burst
        filterMinCutoff: 1.2, // One Euro smoothing floor
        filterBeta: 0.04, // speed-dependent smoothing amount
        filterDCutoff: 1.0 // derivative cutoff
      },
      colors: {
        auraHueMin: 190, // cool color for slow fingertips
        auraHueMax: 330, // warm color for fast fingertips
        orbHue: 285, // orb base hue
        trailHue: 285, // thrown orb trail hue
        burstHue: 35, // throw/bounce burst hue
        lightningHue: 195 // arc hue
      }
    };

    const EFFECTS = {
      aura: {
        trigger: "fingertip_motion",
        count: 2,
        color: "speed_hue",
        lifetime: [0.35, 1.15]
      },
      orb: {
        trigger: "pinch_start",
        count: 0,
        color: "orb_hue",
        lifetime: 6.0
      },
      throw: {
        trigger: "armed_pinch_end_with_velocity",
        count: 42,
        color: "burst_hue",
        lifetime: 0.75
      },
      lightning: {
        trigger: "two_hands_armed_and_close",
        count: 3,
        color: "lightning_hue",
        lifetime: 0.35
      },
      trail: {
        trigger: "thrown_orb_motion",
        count: 1,
        color: "trail_hue",
        lifetime: 0.42
      },
      burst: {
        trigger: "orb_bounce_or_expiry",
        count: 30,
        color: "random_hue",
        lifetime: 0.65
      }
    };

    const injected = __MH_CONFIG__;

    function isPlainObject(v) {
      return v && typeof v === "object" && !Array.isArray(v);
    }

    function merge(base, patch) {
      if (!isPlainObject(base)) return patch;
      const out = { ...base };
      if (isPlainObject(patch)) {
        for (const k of Object.keys(patch)) {
          out[k] = isPlainObject(patch[k]) ? merge(out[k], patch[k]) : patch[k];
        }
      }
      return out;
    }

    function clamp(v, a, b) {
      return v < a ? a : v > b ? b : v;
    }

    function lerp(a, b, t) {
      return a + (b - a) * t;
    }

    function mapRange(v, inMin, inMax, outMin, outMax) {
      const t = clamp((v - inMin) / Math.max(1e-6, inMax - inMin), 0, 1);
      return lerp(outMin, outMax, t);
    }

    function hysteresis(on, value, start, end) {
      if (!on && value < start) return true;
      if (on && value > end) return false;
      return on;
    }

    function bounceValue(pos, vel, min, max, restitution) {
      if (pos < min) {
        pos = min;
        vel = -vel * restitution;
      }
      if (pos > max) {
        pos = max;
        vel = -vel * restitution;
      }
      return { pos, vel };
    }

    const cfg = merge(DEFAULT_CONFIG, injected);

    cfg.quality = clamp(cfg.quality | 0, 1, 5);
    cfg.maxVolume = clamp(Number(cfg.maxVolume) || 0, 0, 0.20);
    cfg.thresholds.pinchEnd = Math.max(cfg.thresholds.pinchEnd, cfg.thresholds.pinchStart + 0.03);

    const canvas = document.getElementById("mh-canvas");
    const ctx = canvas.getContext("2d", { alpha: false });
    const video = document.getElementById("cam");
    const demoVideo = document.getElementById("demo-video");
    const downloadLink = document.getElementById("download-demo");
    const hud = document.getElementById("hud");
    const privacy = document.getElementById("privacy");
    const statusEl = document.getElementById("status");
    const eventLog = document.getElementById("event-log");

    const btnCamera = document.getElementById("btn-camera");
    const btnRecord = document.getElementById("btn-record");
    const btnDelete = document.getElementById("btn-delete");
    const btnAura = document.getElementById("btn-aura");
    const btnOrb = document.getElementById("btn-orb");
    const btnThrow = document.getElementById("btn-throw");
    const btnLightning = document.getElementById("btn-lightning");
    const btnTrails = document.getElementById("btn-trails");
    const btnBursts = document.getElementById("btn-bursts");
    const btnSound = document.getElementById("btn-sound");

    const qualitySlider = document.getElementById("quality");
    const qualityValue = document.getElementById("quality-value");

    const W = 960;
    const H = 540;

    let fps = 60;
    let lastFrameTime = performance.now();
    let lastQualityCheck = 0;
    let effectiveQuality = cfg.quality;
    let lastHud = 0;
    let lastZap = 0;
    let latencyEMA = 0;
    let synthChecks = 0;
    let synthCorrect = 0;
    let lastMpTs = -1;
    let lastCameraHandAt = 0;

    const state = {
      cameraOn: false,
      cameraStream: null,
      newVideoFrame: false,
      lastVideoTime: -1,
      recording: false
    };

    const mp = {
      ready: false,
      loading: false,
      error: "",
      vision: null,
      handLandmarker: null,
      gestureRecognizer: null
    };

    let audioCtx = null;
    let masterGain = null;
    let noiseBuffer = null;

    let recorder = null;
    let chunks = [];
    let demoVideoUrl = null;

    const pointer = {
      x: W * 0.5,
      y: H * 0.55,
      px: W * 0.5,
      py: H * 0.55,
      active: false
    };

    const recentEvents = [];
    const tests = [];
    let testsPassed = 0;
    let testsTotal = 0;
    let statusText = "Starting...";

    class IndexPool {
      constructor(capacity) {
        this.cap = capacity;
        this.stack = new Int32Array(capacity);
        this.top = capacity;
        this.reset();
      }

      reset() {
        this.top = this.cap;
        for (let i = 0; i < this.cap; i++) {
          this.stack[i] = this.cap - 1 - i;
        }
      }

      alloc() {
        if (this.top <= 0) return -1;
        return this.stack[--this.top];
      }

      release(i) {
        if (i >= 0 && i < this.cap) {
          this.stack[this.top++] = i;
        }
      }

      used() {
        return this.cap - this.top;
      }
    }

    class LowPass {
      constructor() {
        this.initialized = false;
        this.y = 0;
      }

      filter(x, alpha) {
        if (!this.initialized || alpha >= 1) {
          this.y = x;
          this.initialized = true;
        } else {
          this.y = alpha * x + (1 - alpha) * this.y;
        }
        return this.y;
      }

      reset() {
        this.initialized = false;
        this.y = 0;
      }
    }

    class OneEuro {
      constructor() {
        this.lastTime = null;
        this.lastRaw = null;
        this.xFilter = new LowPass();
        this.dxFilter = new LowPass();
      }

      reset() {
        this.lastTime = null;
        this.lastRaw = null;
        this.xFilter.reset();
        this.dxFilter.reset();
      }

      filter(x, t) {
        if (this.lastTime === null) {
          this.lastTime = t;
          this.lastRaw = x;
          return this.xFilter.filter(x, 1);
        }

        const dt = (t - this.lastTime) / 1000;
        this.lastTime = t;

        if (dt <= 0) {
          return this.xFilter.y;
        }

        const dx = (x - this.lastRaw) / dt;
        this.lastRaw = x;

        const alphaFor = (cutoff) => 1 / (1 + 1 / (2 * Math.PI * cutoff * dt));

        const filteredDx = this.dxFilter.filter(dx, alphaFor(cfg.thresholds.filterDCutoff));
        const cutoff = cfg.thresholds.filterMinCutoff + cfg.thresholds.filterBeta * Math.abs(filteredDx);
        const alpha = alphaFor(cutoff);

        return this.xFilter.filter(x, alpha);
      }
    }

    const colorCache = new Array(360);
    for (let h = 0; h < 360; h++) {
      colorCache[h] = `hsl(${h}, 95%, 62%)`;
    }

    const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
    bgGrad.addColorStop(0, "#070b18");
    bgGrad.addColorStop(1, "#111827");

    const CONN = new Int16Array([
      0, 1, 1, 2, 2, 3, 3, 4,
      0, 5, 5, 6, 6, 7, 7, 8,
      5, 9, 9, 10, 10, 11, 11, 12,
      9, 13, 13, 14, 14, 15, 15, 16,
      13, 17, 17, 18, 18, 19, 19, 20,
      0, 17
    ]);

    const TIPS = new Int16Array([4, 8, 12, 16, 20]);
    const PALM_IDS = new Int16Array([0, 5, 9, 13, 17]);
    const HAND_FINGER_BASES = new Int16Array([5, 9, 13, 17]);
    const HAND_FINGER_TIPS = new Int16Array([8, 12, 16, 20]);

    const particlePool = new IndexPool(cfg.particleCapacity);
    const partX = new Float32Array(cfg.particleCapacity);
    const partY = new Float32Array(cfg.particleCapacity);
    const partVX = new Float32Array(cfg.particleCapacity);
    const partVY = new Float32Array(cfg.particleCapacity);
    const partLife = new Float32Array(cfg.particleCapacity);
    const partMaxLife = new Float32Array(cfg.particleCapacity);
    const partHue = new Uint16Array(cfg.particleCapacity);
    const partSize = new Float32Array(cfg.particleCapacity);
    const partKind = new Uint8Array(cfg.particleCapacity);
    const partAlive = new Uint8Array(cfg.particleCapacity);

    const orbPool = new IndexPool(cfg.orbCapacity);
    const orbX = new Float32Array(cfg.orbCapacity);
    const orbY = new Float32Array(cfg.orbCapacity);
    const orbPX = new Float32Array(cfg.orbCapacity);
    const orbPY = new Float32Array(cfg.orbCapacity);
    const orbVX = new Float32Array(cfg.orbCapacity);
    const orbVY = new Float32Array(cfg.orbCapacity);
    const orbR = new Float32Array(cfg.orbCapacity);
    const orbLife = new Float32Array(cfg.orbCapacity);
    const orbMaxLife = new Float32Array(cfg.orbCapacity);
    const orbActive = new Uint8Array(cfg.orbCapacity);
    const orbHeld = new Uint8Array(cfg.orbCapacity);
    const orbHand = new Int8Array(cfg.orbCapacity);
    const orbBurstCooldown = new Float32Array(cfg.orbCapacity);

    function currentMaxParticles() {
      const q = clamp(effectiveQuality | 0, 1, 5);
      return cfg.maxParticlesByQuality[q - 1];
    }

    function canSpawnParticle() {
      return particlePool.used() < currentMaxParticles();
    }

    function releaseParticle(i) {
      if (i >= 0 && i < cfg.particleCapacity && partAlive[i]) {
        partAlive[i] = 0;
        partLife[i] = 0;
        particlePool.release(i);
      }
    }

    function spawnParticle(x, y, vx, vy, life, hue, size, kind) {
      const i = particlePool.alloc();
      if (i < 0) return -1;

      partX[i] = x;
      partY[i] = y;
      partVX[i] = vx;
      partVY[i] = vy;
      partLife[i] = life;
      partMaxLife[i] = life;
      partHue[i] = clamp(hue | 0, 0, 359);
      partSize[i] = size;
      partKind[i] = kind;
      partAlive[i] = 1;

      return i;
    }

    function makeHand(side) {
      const filters = [];
      for (let i = 0; i < 21; i++) {
        filters.push({ x: new OneEuro(), y: new OneEuro() });
      }

      return {
        side,
        visible: false,
        source: "demo",
        lm: new Float32Array(42),
        tmp: new Float32Array(42),
        prevTips: new Float32Array(10),
        hasPrev: false,
        filters,
        palmWidth: 1,
        palmCx: 0.5,
        palmCy: 0.5,
        pinch: 1,
        openScore: 0,
        pinchOn: false,
        armed: false,
        armStart: 0,
        armUntil: 0,
        lastActionMs: -99999,
        gestureLabel: "",
        orb: -1,
        intentPinch: false,
        intentOpen: true,
        intentChangedAt: 0,
        histX: new Float32Array(48),
        histY: new Float32Array(48),
        histT: new Float32Array(48),
        histHead: 0,
        histCount: 0
      };
    }

    const hands = [makeHand(0), makeHand(1)];

    function releaseOrb(i) {
      if (i >= 0 && i < cfg.orbCapacity && orbActive[i]) {
        orbActive[i] = 0;
        orbLife[i] = 0;
        orbHeld[i] = 0;
        orbBurstCooldown[i] = 0;

        const h = orbHand[i];
        if (h >= 0 && h < hands.length && hands[h].orb === i) {
          hands[h].orb = -1;
        }

        orbHand[i] = -1;
        orbPool.release(i);
      }
    }

    function resetHand(hand) {
      hand.visible = false;
      hand.pinchOn = false;
      hand.armed = false;
      hand.armStart = 0;
      hand.armUntil = 0;
      hand.hasPrev = false;
      hand.gestureLabel = "";
      hand.histHead = 0;
      hand.histCount = 0;
      hand.intentChangedAt = 0;

      if (hand.orb >= 0) {
        releaseOrb(hand.orb);
      }

      for (const f of hand.filters) {
        f.x.reset();
        f.y.reset();
      }
    }

    function spawnOrbForHand(hand, now) {
      if (hand.orb >= 0) releaseOrb(hand.orb);

      let i = orbPool.alloc();

      if (i < 0) {
        let victim = -1;
        let minLife = 1e9;
        for (let j = 0; j < cfg.orbCapacity; j++) {
          if (orbActive[j] && orbLife[j] < minLife) {
            minLife = orbLife[j];
            victim = j;
          }
        }
        if (victim >= 0) releaseOrb(victim);
        i = orbPool.alloc();
      }

      if (i < 0) return -1;

      orbActive[i] = 1;
      orbX[i] = hand.palmCx * W;
      orbY[i] = hand.palmCy * H;
      orbPX[i] = orbX[i];
      orbPY[i] = orbY[i];
      orbVX[i] = 0;
      orbVY[i] = 0;
      orbR[i] = 12;
      orbLife[i] = EFFECTS.orb.lifetime;
      orbMaxLife[i] = EFFECTS.orb.lifetime;
      orbHeld[i] = 1;
      orbHand[i] = hand.side;
      orbBurstCooldown[i] = 0;
      hand.orb = i;

      return i;
    }

    function dist(hand, a, b) {
      const dx = hand.lm[2 * a] - hand.lm[2 * b];
      const dy = hand.lm[2 * a + 1] - hand.lm[2 * b + 1];
      return Math.sqrt(dx * dx + dy * dy);
    }

    function computeMetrics(hand) {
      hand.palmWidth = Math.max(dist(hand, 5, 17), 1e-5);

      let sx = 0;
      let sy = 0;
      for (let i = 0; i < PALM_IDS.length; i++) {
        const id = PALM_IDS[i];
        sx += hand.lm[2 * id];
        sy += hand.lm[2 * id + 1];
      }
      hand.palmCx = sx / PALM_IDS.length;
      hand.palmCy = sy / PALM_IDS.length;

      hand.pinch = dist(hand, 4, 8) / hand.palmWidth;

      let ext = 0;
      for (let i = 0; i < HAND_FINGER_TIPS.length; i++) {
        const tip = HAND_FINGER_TIPS[i];
        const base = HAND_FINGER_BASES[i];
        if (dist(hand, tip, 0) > dist(hand, base, 0) * 1.05) {
          ext++;
        }
      }
      hand.openScore = ext / HAND_FINGER_TIPS.length;
    }

    function pushHistory(hand, now) {
      const idx = hand.histHead;
      hand.histX[idx] = hand.palmCx * W;
      hand.histY[idx] = hand.palmCy * H;
      hand.histT[idx] = now;
      hand.histHead = (idx + 1) % hand.histX.length;
      if (hand.histCount < hand.histX.length) hand.histCount++;
    }

    const tmpVel = { vx: 0, vy: 0, speed: 0, rawSpeed: 0 };

    function estimateVelocityFromArrays(out, histX, histY, histT, head, count, curX, curY, curT, windowMs, gain, maxSpeed) {
      const len = histX.length;

      out.vx = 0;
      out.vy = 0;
      out.speed = 0;
      out.rawSpeed = 0;

      if (count < 2) {
        return out;
      }

      const latest = (head - 1 + len) % len;
      const target = curT - windowMs;

      let best = -1;
      let bestDiff = Infinity;

      for (let n = 0; n < count; n++) {
        const idx = (latest - n + len) % len;
        const diff = Math.abs(histT[idx] - target);
        if (diff < bestDiff) {
          bestDiff = diff;
          best = idx;
        }
      }

      if (best < 0) {
        return out;
      }

      const dt = (curT - histT[best]) / 1000;
      if (dt < 0.02) {
        return out;
      }

      const rawVx = (curX - histX[best]) / dt;
      const rawVy = (curY - histY[best]) / dt;
      const rawSpeed = Math.hypot(rawVx, rawVy);

      let vx = rawVx * gain;
      let vy = rawVy * gain;
      let speed = Math.hypot(vx, vy);

      if (speed > maxSpeed) {
        const s = maxSpeed / speed;
        vx *= s;
        vy *= s;
        speed = maxSpeed;
      }

      out.vx = vx;
      out.vy = vy;
      out.speed = speed;
      out.rawSpeed = rawSpeed;
      return out;
    }

    function estimateHandVelocity(hand, now, out) {
      const latest = (hand.histHead - 1 + hand.histX.length) % hand.histX.length;
      return estimateVelocityFromArrays(
        out,
        hand.histX,
        hand.histY,
        hand.histT,
        hand.histHead,
        hand.histCount,
        hand.histX[latest],
        hand.histY[latest],
        hand.histT[latest],
        cfg.thresholds.throwWindowMs,
        cfg.thresholds.throwGain,
        cfg.thresholds.throwMaxSpeed
      );
    }

    function setStatus(msg) {
      statusText = msg;
      if (statusEl) statusEl.textContent = msg;
    }

    function pushEvent(type, hand, confidence, params) {
      recentEvents.unshift({
        type,
        hand: hand.side === 0 ? "left" : "right",
        t_ms: performance.now(),
        confidence,
        params: params || {}
      });
      if (recentEvents.length > 8) recentEvents.pop();
    }

    function emitGesture(type, hand, now, confidence, params) {
      pushEvent(type, hand, confidence, params);
      handleGesture(type, hand, now, confidence, params);
    }

    function releaseOrbForHand(hand, now) {
      const i = hand.orb;
      if (i < 0 || !orbActive[i]) return;

      orbHeld[i] = 0;
      hand.orb = -1;

      const vel = estimateHandVelocity(hand, now, tmpVel);

      if (cfg.effects.throw && hand.armed && vel.rawSpeed > cfg.thresholds.throwMinSpeed) {
        orbVX[i] = vel.vx;
        orbVY[i] = vel.vy;
        hand.armed = false;
        pushEvent("throw", hand, 0.9, { speed: Math.round(vel.rawSpeed) });
        playSound("throw");
        if (cfg.effects.bursts) {
          spawnBurst(orbX[i], orbY[i], vel.rawSpeed, cfg.colors.burstHue, EFFECTS.throw.count);
        }
      } else {
        orbVX[i] = vel.vx * 0.15;
        orbVY[i] = vel.vy * 0.15 - 30;
      }

      orbLife[i] = EFFECTS.orb.lifetime;
      orbMaxLife[i] = EFFECTS.orb.lifetime;
    }

    function handleGesture(type, hand, now, confidence, params) {
      const th = cfg.thresholds;

      if (type === "pinch_start") {
        if (now - hand.lastActionMs < th.refractoryMs) return;
        hand.lastActionMs = now;
        if (cfg.effects.orb) spawnOrbForHand(hand, now);
        playSound("pinch");
      } else if (type === "pinch_end") {
        if (now - hand.lastActionMs < th.refractoryMs) return;
        hand.lastActionMs = now;
        releaseOrbForHand(hand, now);
      }
    }

    function detectGestures(hand, now) {
      const th = cfg.thresholds;

      const newPinch = hysteresis(hand.pinchOn, hand.pinch, th.pinchStart, th.pinchEnd);
      if (newPinch !== hand.pinchOn) {
        hand.pinchOn = newPinch;

        let latency = 0;
        if (hand.intentChangedAt > 0) {
          latency = now - hand.intentChangedAt;
          latencyEMA = latencyEMA === 0 ? latency : latencyEMA * 0.75 + latency * 0.25;
          hand.intentChangedAt = 0;
        }

        emitGesture(newPinch ? "pinch_start" : "pinch_end", hand, now, 0.9, {
          pinch: hand.pinch,
          latency_ms: latency
        });
      }

      if (hand.openScore >= 0.72 && hand.pinch > th.pinchEnd) {
        if (hand.armStart === 0) hand.armStart = now;

        if (!hand.armed && now - hand.armStart >= th.armHoldMs) {
          hand.armed = true;
          hand.armUntil = now + th.armValidMs;
          pushEvent("arm", hand, hand.openScore, {});
          playSound("arm");
        }
      } else {
        hand.armStart = 0;
      }

      if (hand.armed && now > hand.armUntil) {
        hand.armed = false;
      }
    }

    function setHandFromFlat(hand, flat, now, source) {
      if (!hand.visible) {
        for (const f of hand.filters) {
          f.x.reset();
          f.y.reset();
        }
        hand.histHead = 0;
        hand.histCount = 0;
        hand.hasPrev = false;
      }

      hand.visible = true;
      hand.source = source;

      for (let i = 0; i < 21; i++) {
        let x = flat[2 * i];
        let y = flat[2 * i + 1];

        if (source === "camera" && cfg.mirrorCamera) {
          x = 1 - x;
        }

        x = clamp(x, -0.2, 1.2);
        y = clamp(y, -0.2, 1.2);

        hand.lm[2 * i] = hand.filters[i].x.filter(x, now);
        hand.lm[2 * i + 1] = hand.filters[i].y.filter(y, now);
      }

      computeMetrics(hand);
      pushHistory(hand, now);
      detectGestures(hand, now);
    }

    const SYN_PALM_LOCAL = [0.0, -0.12];
    const SYN_MCP_LOCAL = [
      [-0.06, -0.14],
      [0.00, -0.16],
      [0.06, -0.14],
      [0.11, -0.10]
    ];
    const SYN_OPEN_TIPS_LOCAL = [
      [-0.07, -0.32],
      [0.00, -0.36],
      [0.07, -0.32],
      [0.12, -0.26]
    ];
    const SYN_THUMB_OPEN = [-0.17, -0.20];
    const SYN_FINGER_BASE = new Int16Array([5, 9, 13, 17]);
    const SYN_FINGER_TIP = new Int16Array([8, 12, 16, 20]);
    const SYN_FINGER_J1 = new Int16Array([6, 10, 14, 18]);
    const SYN_FINGER_J2 = new Int16Array([7, 11, 15, 19]);

    const synthBuf = [new Float32Array(42), new Float32Array(42)];
    const synthPrevIntent = [false, false];

    function synthSet(out, idx, lx, ly, cx, cy, scale, cosR, sinR, mirror) {
      if (mirror) lx = -lx;

      const rx = lx * cosR - ly * sinR;
      const ry = lx * sinR + ly * cosR;

      out[2 * idx] = clamp(cx + rx * scale, -0.2, 1.2);
      out[2 * idx + 1] = clamp(cy + ry * scale, -0.2, 1.2);
    }

    function fillSyntheticHand(out, p, mirror) {
      const cosR = Math.cos(p.rot);
      const sinR = Math.sin(p.rot);

      synthSet(out, 0, 0.0, 0.0, p.cx, p.cy, p.scale, cosR, sinR, mirror);
      synthSet(out, 1, -0.04, -0.03, p.cx, p.cy, p.scale, cosR, sinR, mirror);

      let indexTipX = 0;
      let indexTipY = 0;

      for (let f = 0; f < 4; f++) {
        const base = SYN_MCP_LOCAL[f];
        const tip = SYN_OPEN_TIPS_LOCAL[f];

        const tx = SYN_PALM_LOCAL[0] + (tip[0] - SYN_PALM_LOCAL[0]) * p.open;
        const ty = SYN_PALM_LOCAL[1] + (tip[1] - SYN_PALM_LOCAL[1]) * p.open;

        if (f === 0) {
          indexTipX = tx;
          indexTipY = ty;
        }

        const baseIdx = SYN_FINGER_BASE[f];
        const tipIdx = SYN_FINGER_TIP[f];
        const j1 = SYN_FINGER_J1[f];
        const j2 = SYN_FINGER_J2[f];

        synthSet(out, baseIdx, base[0], base[1], p.cx, p.cy, p.scale, cosR, sinR, mirror);
        synthSet(out, j1, base[0] + (tx - base[0]) * 0.35, base[1] + (ty - base[1]) * 0.35, p.cx, p.cy, p.scale, cosR, sinR, mirror);
        synthSet(out, j2, base[0] + (tx - base[0]) * 0.70, base[1] + (ty - base[1]) * 0.70, p.cx, p.cy, p.scale, cosR, sinR, mirror);
        synthSet(out, tipIdx, tx, ty, p.cx, p.cy, p.scale, cosR, sinR, mirror);
      }

      const close = clamp(1 - p.pinch, 0, 1);
      const thumbTipX = SYN_THUMB_OPEN[0] + (indexTipX - SYN_THUMB_OPEN[0]) * close;
      const thumbTipY = SYN_THUMB_OPEN[1] + (indexTipY - SYN_THUMB_OPEN[1]) * close;

      synthSet(out, 4, thumbTipX, thumbTipY, p.cx, p.cy, p.scale, cosR, sinR, mirror);
      synthSet(out, 3, -0.09 + (thumbTipX + 0.09) * 0.65, -0.09 + (thumbTipY + 0.09) * 0.65, p.cx, p.cy, p.scale, cosR, sinR, mirror);
      synthSet(out, 2, -0.05 + (thumbTipX + 0.05) * 0.30, -0.04 + (thumbTipY + 0.04) * 0.30, p.cx, p.cy, p.scale, cosR, sinR, mirror);
    }

    function scoreSynthetic(hand, intentPinch, intentOpen) {
      if (!hand.visible) return;
      synthChecks += 2;
      if (hand.pinchOn === intentPinch) synthCorrect++;
      if ((hand.openScore >= 0.72) === intentOpen) synthCorrect++;
    }

    function updateSynthetic(now) {
      const t = now / 1000;
      const c = t % 14;

      let L = {
        cx: 0.32 + 0.025 * Math.sin(t * 0.7),
        cy: 0.62 + 0.020 * Math.cos(t * 0.6),
        scale: 0.20,
        rot: 0.05 * Math.sin(t * 0.4),
        open: 1,
        pinch: 1
      };

      let R = {
        cx: 0.68 + 0.025 * Math.sin(t * 0.65 + 1.2),
        cy: 0.62 + 0.020 * Math.cos(t * 0.55 + 2.0),
        scale: 0.20,
        rot: -0.05 * Math.sin(t * 0.45 + 1),
        open: 1,
        pinch: 1
      };

      if (c < 1.6) {
        // Both palms open, arming happens after the hold timer.
      } else if (c < 3.4) {
        // Left pinch grows an orb.
        L.open = 0.35;
        L.pinch = 0.12;
      } else if (c < 3.9) {
        // Left fast throw motion while still pinched.
        const u = (c - 3.4) / 0.5;
        L.open = 0.30;
        L.pinch = 0.12;
        L.cx += 0.22 * u;
        L.cy -= 0.30 * u;
      } else if (c < 4.6) {
        // Left release, orb throws forward.
        const u = (c - 3.9) / 0.7;
        L.open = 0.85;
        L.pinch = 0.85;
        L.cx += 0.22 + 0.06 * u;
        L.cy -= 0.30 + 0.10 * u;
      } else if (c < 6.4) {
        // Both hands open and re-arm.
        L.open = 1;
        R.open = 1;
        L.pinch = 1;
        R.pinch = 1;
      } else if (c < 8.0) {
        // Two-hand lightning window.
        L.cx = 0.43 + 0.020 * Math.sin(t * 10);
        R.cx = 0.57 - 0.020 * Math.sin(t * 10 + 1.7);
        L.cy = 0.46 + 0.020 * Math.cos(t * 8);
        R.cy = 0.46 + 0.020 * Math.cos(t * 8 + 0.6);
        L.open = 0.95;
        R.open = 0.95;
        L.pinch = 0.82;
        R.pinch = 0.82;
      } else if (c < 9.8) {
        // Right pinch grows an orb.
        R.open = 0.35;
        R.pinch = 0.12;
      } else if (c < 10.3) {
        // Right fast throw motion while still pinched.
        const u = (c - 9.8) / 0.5;
        R.open = 0.30;
        R.pinch = 0.12;
        R.cx -= 0.22 * u;
        R.cy -= 0.30 * u;
      } else if (c < 11.0) {
        // Right release, orb throws forward.
        const u = (c - 10.3) / 0.7;
        R.open = 0.85;
        R.pinch = 0.85;
        R.cx -= 0.22 + 0.06 * u;
        R.cy -= 0.30 + 0.10 * u;
      } else {
        // Idle aura and reset.
        L.open = 0.9;
        R.open = 0.9;
        L.pinch = 0.9;
        R.pinch = 0.9;
      }

      const intentL = L.pinch < cfg.thresholds.pinchStart;
      const intentR = R.pinch < cfg.thresholds.pinchStart;
      const openL = L.open > 0.75;
      const openR = R.open > 0.75;

      if (intentL !== synthPrevIntent[0]) {
        hands[0].intentChangedAt = now;
        synthPrevIntent[0] = intentL;
      }

      if (intentR !== synthPrevIntent[1]) {
        hands[1].intentChangedAt = now;
        synthPrevIntent[1] = intentR;
      }

      hands[0].intentPinch = intentL;
      hands[1].intentPinch = intentR;
      hands[0].intentOpen = openL;
      hands[1].intentOpen = openR;

      fillSyntheticHand(synthBuf[0], L, false);
      fillSyntheticHand(synthBuf[1], R, true);

      setHandFromFlat(hands[0], synthBuf[0], now, "demo");
      setHandFromFlat(hands[1], synthBuf[1], now, "demo");

      scoreSynthetic(hands[0], intentL, openL);
      scoreSynthetic(hands[1], intentR, openR);
    }

    async function createHandLandmarker(vision, fileset, delegate) {
      const opts = {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
          delegate
        },
        runningMode: "VIDEO",
        numHands: 2
      };

      try {
        return await vision.HandLandmarker.createFromOptions(fileset, opts);
      } catch (e) {
        if (delegate === "GPU") {
          return createHandLandmarker(vision, fileset, "CPU");
        }
        throw e;
      }
    }

    async function createGestureRecognizer(vision, fileset, delegate) {
      const opts = {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task",
          delegate
        },
        runningMode: "VIDEO",
        numHands: 2
      };

      try {
        return await vision.GestureRecognizer.createFromOptions(fileset, opts);
      } catch (e) {
        if (delegate === "GPU") {
          return createGestureRecognizer(vision, fileset, "CPU");
        }
        throw e;
      }
    }

    async function initMediaPipe() {
      if (mp.ready || mp.loading) return;

      mp.loading = true;
      setStatus("Loading MediaPipe Tasks...");

      try {
        const vision = await import("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/vision_bundle.mjs");
        const fileset = await vision.FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm");

        mp.vision = vision;
        mp.handLandmarker = await createHandLandmarker(vision, fileset, "GPU");

        try {
          mp.gestureRecognizer = await createGestureRecognizer(vision, fileset, "GPU");
        } catch (e) {
          mp.gestureRecognizer = null;
        }

        mp.ready = true;
        mp.error = "";
        lastMpTs = -1;
        setStatus("MediaPipe ready. Show one or two hands to the camera.");
      } catch (e) {
        mp.error = e && e.message ? e.message : String(e);
        mp.ready = false;
        setStatus("MediaPipe unavailable (" + mp.error + "). Synthetic demo remains active.");
      }
    }

    function scheduleVideoCallback() {
      if (!state.cameraOn) return;

      if (video.requestVideoFrameCallback) {
        video.requestVideoFrameCallback(() => {
          state.newVideoFrame = true;
          scheduleVideoCallback();
        });
      }
    }

    async function enableCamera() {
      if (state.cameraOn) return;

      try {
        setStatus("Requesting camera...");

        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: "user"
          },
          audio: false
        });

        state.cameraStream = stream;
        video.srcObject = stream;
        await video.play();

        state.cameraOn = true;
        state.newVideoFrame = false;
        state.lastVideoTime = -1;
        lastMpTs = -1;
        lastCameraHandAt = performance.now();

        btnCamera.textContent = "Disable camera";
        btnCamera.classList.add("on");
        privacy.textContent = "Camera ON • local processing • no upload";

        scheduleVideoCallback();
        await initMediaPipe();
      } catch (e) {
        setStatus("Camera unavailable: " + (e && e.message ? e.message : String(e)));
        state.cameraOn = false;
      }
    }

    function disableCamera() {
      if (state.cameraStream) {
        for (const track of state.cameraStream.getTracks()) {
          track.stop();
        }
        state.cameraStream = null;
      }

      video.srcObject = null;
      state.cameraOn = false;
      state.newVideoFrame = false;
      state.lastVideoTime = -1;
      lastMpTs = -1;

      btnCamera.textContent = "Enable camera";
      btnCamera.classList.remove("on");
      privacy.textContent = "Camera OFF • local only • no upload";

      resetHand(hands[0]);
      resetHand(hands[1]);
    }

    function applyMediaPipeResult(result, now) {
      const lms = result.landmarks || [];
      const count = Math.min(lms.length, 2);

      if (count > 0) {
        lastCameraHandAt = now;
      }

      for (let k = 0; k < count; k++) {
        const hand = hands[k];
        const pts = lms[k];

        for (let i = 0; i < 21; i++) {
          hand.tmp[2 * i] = pts[i].x;
          hand.tmp[2 * i + 1] = pts[i].y;
        }

        setHandFromFlat(hand, hand.tmp, now, "camera");

        if (result.gestures && result.gestures[k] && result.gestures[k].length) {
          hand.gestureLabel = result.gestures[k][0].categoryName || "";
        } else {
          hand.gestureLabel = "";
        }
      }

      for (let k = count; k < 2; k++) {
        resetHand(hands[k]);
      }
    }

    function processCameraIfNeeded(now) {
      if (!mp.ready) return;

      if (!video.requestVideoFrameCallback && video.currentTime !== state.lastVideoTime) {
        state.lastVideoTime = video.currentTime;
        state.newVideoFrame = true;
      }

      if (!state.newVideoFrame) return;
      state.newVideoFrame = false;

      if (video.readyState < 2) return;

      const ts = Math.max(now, lastMpTs + 1);
      lastMpTs = ts;

      let result = null;

      try {
        if (mp.gestureRecognizer) {
          result = mp.gestureRecognizer.detectForVideo(video, ts);
        } else if (mp.handLandmarker) {
          result = mp.handLandmarker.detectForVideo(video, ts);
        }
      } catch (e) {
        mp.error = e && e.message ? e.message : String(e);
        setStatus("Tracking error: " + mp.error);
        return;
      }

      if (result && result.landmarks) {
        applyMediaPipeResult(result, ts);
      }
    }

    function unlockAudio() {
      if (audioCtx) {
        if (audioCtx.state === "suspended") audioCtx.resume();
        return;
      }

      try {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;

        audioCtx = new AC();
        masterGain = audioCtx.createGain();
        masterGain.gain.value = cfg.soundEnabled ? cfg.maxVolume : 0;
        masterGain.connect(audioCtx.destination);

        noiseBuffer = audioCtx.createBuffer(1, Math.floor(audioCtx.sampleRate * 0.5), audioCtx.sampleRate);
        const d = noiseBuffer.getChannelData(0);
        for (let i = 0; i < d.length; i++) {
          d[i] = Math.random() * 2 - 1;
        }
      } catch (e) {
        audioCtx = null;
        masterGain = null;
        noiseBuffer = null;
      }
    }

    function playTone(type, f0, f1, dur, gainValue) {
      if (!audioCtx || !masterGain || !cfg.soundEnabled) return;

      const t = audioCtx.currentTime;
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();

      o.type = type;
      o.frequency.setValueAtTime(f0, t);
      if (f1 !== f0) {
        o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
      }

      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(gainValue, t + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);

      o.connect(g);
      g.connect(masterGain);

      o.start(t);
      o.stop(t + dur + 0.02);
      o.onended = () => g.disconnect();
    }

    function playNoise(dur, freq, q, gainValue) {
      if (!audioCtx || !masterGain || !noiseBuffer || !cfg.soundEnabled) return;

      const t = audioCtx.currentTime;
      const src = audioCtx.createBufferSource();
      const filter = audioCtx.createBiquadFilter();
      const g = audioCtx.createGain();

      src.buffer = noiseBuffer;
      filter.type = "bandpass";
      filter.frequency.value = freq;
      filter.Q.value = q;

      g.gain.setValueAtTime(gainValue, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);

      src.connect(filter);
      filter.connect(g);
      g.connect(masterGain);

      src.start(t);
      src.stop(t + dur + 0.02);
      src.onended = () => {
        g.disconnect();
        filter.disconnect();
      };
    }

    function playSound(kind) {
      if (!audioCtx || !masterGain || !cfg.soundEnabled) return;
      if (audioCtx.state === "suspended") audioCtx.resume();

      if (kind === "pinch") {
        playTone("sine", 820, 1320, 0.12, 0.45);
      } else if (kind === "arm") {
        playTone("triangle", 520, 520, 0.08, 0.35);
        window.setTimeout(() => playTone("triangle", 780, 780, 0.10, 0.35), 85);
      } else if (kind === "throw") {
        playTone("sawtooth", 180, 760, 0.22, 0.55);
        playNoise(0.18, 1100, 0.7, 0.35);
      } else if (kind === "zap") {
        playNoise(0.16, 2300, 0.8, 0.50);
        playTone("square", 1400, 500, 0.10, 0.25);
      } else if (kind === "bounce") {
        playTone("sine", 150, 80, 0.12, 0.35);
        playNoise(0.08, 420, 0.8, 0.20);
      }
    }

    function spawnBurst(x, y, power, hue, maxCount) {
      if (!cfg.effects.bursts) return;

      const cap = maxCount || EFFECTS.burst.count;
      const count = Math.min(cap, 8 + Math.floor(power / 60));

      for (let i = 0; i < count; i++) {
        if (!canSpawnParticle()) break;

        const ang = Math.random() * Math.PI * 2;
        const sp = 70 + Math.random() * Math.max(80, power * 0.55);
        const life = EFFECTS.burst.lifetime * (0.55 + Math.random() * 0.85);
        const size = 1.4 + Math.random() * 3.2;
        const h = hue >= 0 ? hue : Math.floor(Math.random() * 360);

        spawnParticle(
          x,
          y,
          Math.cos(ang) * sp,
          Math.sin(ang) * sp,
          life,
          h,
          size,
          3
        );
      }
    }

    function emitAura(dt, now) {
      if (dt <= 0) return;

      const th = cfg.thresholds;

      if (cfg.effects.aura) {
        for (const hand of hands) {
          if (!hand.visible) continue;

          for (let k = 0; k < TIPS.length; k++) {
            const idx = TIPS[k];
            const x = hand.lm[2 * idx] * W;
            const y = hand.lm[2 * idx + 1] * H;

            let speed = 0;
            let tvx = 0;
            let tvy = 0;

            if (hand.hasPrev) {
              const px = hand.prevTips[2 * k];
              const py = hand.prevTips[2 * k + 1];
              tvx = (x - px) / dt;
              tvy = (y - py) / dt;
              speed = Math.hypot(tvx, tvy);
            }

            const norm = clamp(speed / th.auraMaxSpeed, 0, 1);
            const hue = mapRange(norm, 0, 1, cfg.colors.auraHueMin, cfg.colors.auraHueMax) | 0;
            let count = EFFECTS.aura.count + Math.floor(norm * 5);

            if (!canSpawnParticle()) count = 0;

            for (let c = 0; c < count && canSpawnParticle(); c++) {
              const ang = Math.random() * Math.PI * 2;
              const sp = 15 + Math.random() * 55 + speed * 0.08;
              const vx = Math.cos(ang) * sp + tvx * 0.12;
              const vy = Math.sin(ang) * sp + tvy * 0.12;
              const life = lerp(EFFECTS.aura.lifetime[0], EFFECTS.aura.lifetime[1], Math.random());
              const size = 1.5 + Math.random() * 2.5 + norm * 2;

              spawnParticle(x, y, vx, vy, life, hue, size, 1);
            }
          }
        }

        if (pointer.active) {
          const dx = pointer.x - pointer.px;
          const dy = pointer.y - pointer.py;
          const speed = Math.hypot(dx, dy) / dt;
          const norm = clamp(speed / th.auraMaxSpeed, 0, 1);
          const hue = mapRange(norm, 0, 1, cfg.colors.auraHueMin, cfg.colors.auraHueMax) | 0;
          let count = 1 + Math.floor(norm * 5);

          if (!canSpawnParticle()) count = 0;

          for (let c = 0; c < count && canSpawnParticle(); c++) {
            const ang = Math.random() * Math.PI * 2;
            const sp = 10 + Math.random() * 45 + speed * 0.05;
            const vx = Math.cos(ang) * sp + (dx / dt) * 0.08;
            const vy = Math.sin(ang) * sp + (dy / dt) * 0.08;
            const life = lerp(EFFECTS.aura.lifetime[0], EFFECTS.aura.lifetime[1], Math.random());
            const size = 1.2 + Math.random() * 2.2 + norm * 1.8;

            spawnParticle(pointer.x, pointer.y, vx, vy, life, hue, size, 1);
          }
        }
      }

      for (const hand of hands) {
        if (hand.visible) {
          for (let k = 0; k < TIPS.length; k++) {
            const idx = TIPS[k];
            hand.prevTips[2 * k] = hand.lm[2 * idx] * W;
            hand.prevTips[2 * k + 1] = hand.lm[2 * idx + 1] * H;
          }
        }
        hand.hasPrev = hand.visible;
      }

      if (pointer.active) {
        pointer.px = pointer.x;
        pointer.py = pointer.y;
      }
    }

    function updateParticles(dt) {
      const damp = Math.pow(cfg.thresholds.damping, dt * 60);

      for (let i = 0; i < cfg.particleCapacity; i++) {
        if (!partAlive[i]) continue;

        partLife[i] -= dt;

        if (partLife[i] <= 0) {
          releaseParticle(i);
          continue;
        }

        if (partKind[i] === 3) {
          const burstDamp = Math.pow(0.96, dt * 60);
          partVX[i] *= burstDamp;
          partVY[i] *= burstDamp;
          partVY[i] += cfg.thresholds.gravity * 0.45 * dt;
        } else if (partKind[i] === 2) {
          partVX[i] *= damp;
          partVY[i] *= damp;
        } else {
          partVX[i] *= damp;
          partVY[i] *= damp;
          partVY[i] -= 18 * dt;
        }

        partX[i] += partVX[i] * dt;
        partY[i] += partVY[i] * dt;

        if (partX[i] < -80 || partX[i] > W + 80 || partY[i] < -80 || partY[i] > H + 80) {
          releaseParticle(i);
        }
      }
    }

    function updateOrbs(dt, now) {
      const th = cfg.thresholds;

      for (let i = 0; i < cfg.orbCapacity; i++) {
        if (!orbActive[i]) continue;

        if (orbBurstCooldown[i] > 0) {
          orbBurstCooldown[i] = Math.max(0, orbBurstCooldown[i] - dt);
        }

        if (orbHeld[i]) {
          const h = hands[orbHand[i]];

          if (h && h.visible && h.pinchOn) {
            const closeness = clamp((th.pinchEnd - h.pinch) / Math.max(1e-5, th.pinchEnd - th.pinchStart), 0, 1);
            const target = 10 + closeness * 82;
            orbR[i] += (target - orbR[i]) * Math.min(1, dt * 9);
            orbPX[i] = orbX[i];
            orbPY[i] = orbY[i];
            orbX[i] = h.palmCx * W;
            orbY[i] = h.palmCy * H;

            if (Math.random() < 0.28 && canSpawnParticle()) {
              const ang = Math.random() * Math.PI * 2;
              const rr = orbR[i] * 0.72;
              spawnParticle(
                orbX[i] + Math.cos(ang) * rr,
                orbY[i] + Math.sin(ang) * rr,
                Math.cos(ang) * 22,
                Math.sin(ang) * 22,
                0.35,
                cfg.colors.orbHue,
                2,
                1
              );
            }
          } else {
            orbHeld[i] = 0;
            if (h) h.orb = -1;
          }
        } else {
          orbPX[i] = orbX[i];
          orbPY[i] = orbY[i];

          orbVY[i] += th.gravity * dt;
          orbX[i] += orbVX[i] * dt;
          orbY[i] += orbVY[i] * dt;

          const speed = Math.hypot(orbVX[i], orbVY[i]);

          if (cfg.effects.trails && speed > th.trailSpeed && Math.random() < 0.65 && canSpawnParticle()) {
            spawnParticle(
              orbX[i] + (Math.random() - 0.5) * orbR[i] * 0.45,
              orbY[i] + (Math.random() - 0.5) * orbR[i] * 0.45,
              -orbVX[i] * 0.04 + (Math.random() - 0.5) * 25,
              -orbVY[i] * 0.04 + (Math.random() - 0.5) * 25,
              EFFECTS.trail.lifetime,
              cfg.colors.trailHue,
              1.8 + Math.random() * 2.2,
              2
            );
          }

          let bounced = false;
          let impact = 0;

          if (orbX[i] < orbR[i]) {
            impact = Math.abs(orbVX[i]);
            orbX[i] = orbR[i];
            orbVX[i] = -orbVX[i] * th.bounce;
            bounced = true;
          } else if (orbX[i] > W - orbR[i]) {
            impact = Math.abs(orbVX[i]);
            orbX[i] = W - orbR[i];
            orbVX[i] = -orbVX[i] * th.bounce;
            bounced = true;
          }

          if (orbY[i] < orbR[i]) {
            impact = Math.max(impact, Math.abs(orbVY[i]));
            orbY[i] = orbR[i];
            orbVY[i] = -orbVY[i] * th.bounce;
            bounced = true;
          } else if (orbY[i] > H - orbR[i]) {
            impact = Math.max(impact, Math.abs(orbVY[i]));
            orbY[i] = H - orbR[i];
            orbVY[i] = -orbVY[i] * th.bounce;
            bounced = true;
          }

          if (bounced && impact > th.burstMinImpact && orbBurstCooldown[i] <= 0) {
            orbBurstCooldown[i] = 0.18;
            spawnBurst(orbX[i], orbY[i], impact, cfg.colors.burstHue, 18);
            playSound("bounce");
          }

          orbLife[i] -= dt;

          if (orbLife[i] <= 0) {
            spawnBurst(orbX[i], orbY[i], 220, cfg.colors.orbHue, 24);
            releaseOrb(i);
          }
        }
      }
    }

    function lightningActive() {
      if (!cfg.effects.lightning) return false;

      const h0 = hands[0];
      const h1 = hands[1];

      if (!h0.visible || !h1.visible) return false;

      const dx = h0.palmCx - h1.palmCx;
      const dy = h0.palmCy - h1.palmCy;
      const avgW = Math.max(1e-5, (h0.palmWidth + h1.palmWidth) * 0.5);
      const norm = Math.hypot(dx, dy) / avgW;

      return norm < cfg.thresholds.lightningMaxPalmDist && (h0.armed || h1.armed);
    }

    function drawJagged(x1, y1, x2, y2, segments, amp, depth) {
      ctx.beginPath();
      ctx.moveTo(x1, y1);

      let lx = x1;
      let ly = y1;

      for (let i = 1; i < segments; i++) {
        const t = i / segments;
        const nx = x1 + (x2 - x1) * t + (Math.random() - 0.5) * amp;
        const ny = y1 + (y2 - y1) * t + (Math.random() - 0.5) * amp;
        ctx.lineTo(nx, ny);
        lx = nx;
        ly = ny;
      }

      ctx.lineTo(x2, y2);
      ctx.stroke();

      if (depth > 1) {
        const mx = (x1 + x2) * 0.5 + (Math.random() - 0.5) * amp;
        const my = (y1 + y2) * 0.5 + (Math.random() - 0.5) * amp;
        const bx = mx + (x2 - x1) * 0.18 + (Math.random() - 0.5) * amp;
        const by = my + (y2 - y1) * 0.18 + (Math.random() - 0.5) * amp;
        drawJagged(mx, my, bx, by, 7, amp * 0.55, depth - 1);
      }
    }

    function drawLightning(now) {
      if (!lightningActive()) return;

      const h0 = hands[0];
      const h1 = hands[1];

      const x1 = h0.lm[2 * 8] * W;
      const y1 = h0.lm[2 * 8 + 1] * H;
      const x2 = h1.lm[2 * 8] * W;
      const y2 = h1.lm[2 * 8 + 1] * H;

      const dx = h0.palmCx - h1.palmCx;
      const dy = h0.palmCy - h1.palmCy;
      const avgW = Math.max(1e-5, (h0.palmWidth + h1.palmWidth) * 0.5);
      const norm = Math.hypot(dx, dy) / avgW;
      const strength = clamp(1 - norm / cfg.thresholds.lightningMaxPalmDist, 0, 1);

      ctx.globalCompositeOperation = "lighter";
      ctx.strokeStyle = colorCache[cfg.colors.lightningHue];
      ctx.lineWidth = 1.5 + strength * 2.0;
      ctx.globalAlpha = 0.72 + strength * 0.22;

      drawJagged(x1, y1, x2, y2, 14 + Math.floor(strength * 10), 18 + strength * 22, 2);

      if (cfg.effects.aura) {
        for (let i = 0; i < EFFECTS.lightning.count; i++) {
          if (!canSpawnParticle()) break;
          const t = Math.random();
          const x = lerp(x1, x2, t) + (Math.random() - 0.5) * 24;
          const y = lerp(y1, y2, t) + (Math.random() - 0.5) * 24;
          spawnParticle(
            x,
            y,
            (Math.random() - 0.5) * 120,
            (Math.random() - 0.5) * 120,
            EFFECTS.lightning.lifetime,
            cfg.colors.lightningHue,
            1.2 + Math.random() * 2.0,
            3
          );
        }
      }

      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";

      if (now - lastZap > 650) {
        playSound("zap");
        lastZap = now;
      }
    }

    function drawGrid() {
      ctx.strokeStyle = "rgba(148, 163, 184, 0.08)";
      ctx.lineWidth = 1;

      for (let x = 0; x <= W; x += 80) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, H);
        ctx.stroke();
      }

      for (let y = 0; y <= H; y += 80) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(W, y);
        ctx.stroke();
      }
    }

    function drawParticles() {
      ctx.globalCompositeOperation = "lighter";

      for (let i = 0; i < cfg.particleCapacity; i++) {
        if (!partAlive[i]) continue;

        const a = clamp(partLife[i] / Math.max(1e-5, partMaxLife[i]), 0, 1);
        const s = partSize[i] * (0.55 + a * 0.75);

        ctx.globalAlpha = a * 0.82;
        ctx.fillStyle = colorCache[partHue[i]];
        ctx.fillRect(partX[i] - s * 0.5, partY[i] - s * 0.5, s, s);
      }

      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";
    }

    function drawOrbs() {
      ctx.globalCompositeOperation = "lighter";

      for (let i = 0; i < cfg.orbCapacity; i++) {
        if (!orbActive[i]) continue;

        const a = clamp(orbLife[i] / Math.max(1e-5, orbMaxLife[i]), 0, 1);
        const r = Math.max(4, orbR[i]);

        const grad = ctx.createRadialGradient(orbX[i], orbY[i], 0, orbX[i], orbY[i], r);
        grad.addColorStop(0, `hsla(${cfg.colors.orbHue}, 95%, 82%, ${0.55 * a + 0.22})`);
        grad.addColorStop(0.45, `hsla(${cfg.colors.orbHue}, 92%, 62%, ${0.32 * a + 0.10})`);
        grad.addColorStop(1, `hsla(${cfg.colors.orbHue}, 90%, 45%, 0)`);

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(orbX[i], orbY[i], r, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.globalCompositeOperation = "source-over";
    }

    function drawHands() {
      if (!cfg.showLandmarks) return;

      ctx.lineWidth = 2;
      ctx.globalCompositeOperation = "source-over";

      for (const hand of hands) {
        if (!hand.visible) continue;

        ctx.strokeStyle = hand.armed ? "#34d399" : hand.pinchOn ? "#f59e0b" : "#22d3ee";

        for (let i = 0; i < CONN.length; i += 2) {
          const a = CONN[i];
          const b = CONN[i + 1];

          ctx.beginPath();
          ctx.moveTo(hand.lm[2 * a] * W, hand.lm[2 * a + 1] * H);
          ctx.lineTo(hand.lm[2 * b] * W, hand.lm[2 * b + 1] * H);
          ctx.stroke();
        }

        ctx.fillStyle = "#ffffff";
        for (let k = 0; k < TIPS.length; k++) {
          const idx = TIPS[k];
          ctx.beginPath();
          ctx.arc(hand.lm[2 * idx] * W, hand.lm[2 * idx + 1] * H, 4, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.fillStyle = "rgba(255,255,255,0.82)";
        ctx.font = "11px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";

        const label =
          (hand.side === 0 ? "L" : "R") +
          " " +
          (hand.armed ? "ARMED " : "") +
          (hand.pinchOn ? "PINCH " : "") +
          (hand.gestureLabel ? hand.gestureLabel : "");

        ctx.fillText(label, hand.palmCx * W + 8, hand.palmCy * H - 8);
      }
    }

    function drawCanvasStatus() {
      ctx.globalCompositeOperation = "source-over";
      ctx.globalAlpha = 1;
      ctx.fillStyle = "rgba(226, 232, 240, 0.72)";
      ctx.font = "12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
      ctx.fillText(statusText, 12, H - 12);
      ctx.fillText("Local only • no upload • click canvas to enable sound", 12, H - 28);
    }

    function draw(now) {
      if (state.cameraOn && video.readyState >= 2) {
        ctx.save();
        if (cfg.mirrorCamera) {
          ctx.translate(W, 0);
          ctx.scale(-1, 1);
        }
        ctx.drawImage(video, 0, 0, W, H);
        ctx.restore();

        ctx.fillStyle = "rgba(3, 7, 18, 0.22)";
        ctx.fillRect(0, 0, W, H);
      } else {
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, W, H);
        drawGrid();
      }

      drawParticles();
      drawOrbs();
      drawLightning(now);
      drawHands();
      drawCanvasStatus();
    }

    function updateFps(now) {
      const dt = now - lastFrameTime;
      lastFrameTime = now;

      if (dt > 0) {
        const inst = 1000 / dt;
        fps = fps * 0.9 + inst * 0.1;
      }

      if (now - lastQualityCheck > 700) {
        lastQualityCheck = now;

        if (fps < cfg.minFps && effectiveQuality > 1) {
          effectiveQuality--;
        } else if (fps > cfg.targetFps - 3 && effectiveQuality < cfg.quality) {
          effectiveQuality++;
        }
      }
    }

    function formatEvent(e) {
      const lat = e.params && e.params.latency_ms ? ` lat=${Math.round(e.params.latency_ms)}ms` : "";
      const spd = e.params && e.params.speed ? ` speed=${e.params.speed}px/s` : "";
      return `${(e.t_ms / 1000).toFixed(2)}s ${e.hand} ${e.type} conf=${e.confidence.toFixed(2)}${lat}${spd}`;
    }

    function updateHud(now) {
      if (now - lastHud < 200) return;
      lastHud = now;

      let evStr = "none";
      if (recentEvents.length) {
        evStr = "";
        for (let i = 0; i < Math.min(recentEvents.length, 5); i++) {
          if (i) evStr += " · ";
          evStr += recentEvents[i].type + ":" + recentEvents[i].hand;
        }
      }

      const acc = synthChecks > 0 ? (100 * synthCorrect / synthChecks) : 0;

      hud.textContent =
        "FPS " +
        fps.toFixed(1) +
        " | particles " +
        particlePool.used() +
        "/" +
        currentMaxParticles() +
        " | orbs " +
        orbPool.used() +
        " | quality " +
        effectiveQuality +
        "/" +
        cfg.quality +
        "\ntests " +
        testsPassed +
        "/" +
        testsTotal +
        " | latency " +
        latencyEMA.toFixed(1) +
        " ms | accuracy " +
        acc.toFixed(1) +
        "%" +
        "\n" +
        evStr;

      if (eventLog) {
        eventLog.textContent = recentEvents.length
          ? recentEvents.map(formatEvent).join("\n")
          : "No events yet.";
      }
    }

    function tick(now) {
      const dt = Math.min(0.05, (now - lastFrameTime) / 1000);

      updateFps(now);

      const trackingCamera = state.cameraOn && mp.ready;
      if (trackingCamera) {
        processCameraIfNeeded(now);
      } else {
        updateSynthetic(now);
      }

      emitAura(dt, now);
      updateOrbs(dt, now);
      updateParticles(dt);
      draw(now);
      updateHud(now);

      requestAnimationFrame(tick);
    }

    function assert(name, cond) {
      const ok = !!cond;
      tests.push({ name, pass: ok });
      if (ok) testsPassed++;
      testsTotal++;
    }

    function runTests() {
      tests.length = 0;
      testsPassed = 0;
      testsTotal = 0;

      const len = 8;
      const hx = new Float32Array(len);
      const hy = new Float32Array(len);
      const ht = new Float32Array(len);

      for (let i = 0; i < 6; i++) {
        hx[i] = i * 20;
        hy[i] = 0;
        ht[i] = i * 20;
      }

      const v = estimateVelocityFromArrays({}, hx, hy, ht, 6, 6, hx[5], hy[5], ht[5], 100, 1, 5000);
      assert("Velocity estimate", Math.abs(v.vx - 1000) < 1 && Math.abs(v.rawSpeed - 1000) < 1);

      const vc = estimateVelocityFromArrays({}, hx, hy, ht, 6, 6, hx[5], hy[5], ht[5], 100, 10, 100);
      assert("Velocity clamp", vc.speed <= 100 + 1e-6);

      const p = new IndexPool(3);
      const a = p.alloc();
      const b = p.alloc();
      const c = p.alloc();
      assert("Particle pool no over-allocation", a !== b && b !== c && p.alloc() === -1);

      p.release(b);
      assert("Particle pool reuse", p.alloc() === b);

      p.release(a);
      p.release(c);
      p.release(b);
      assert("Particle pool empty after release", p.used() === 0);

      const r1 = bounceValue(-5, -100, 0, 100, 0.5);
      assert("Bounce left", Math.abs(r1.pos) < 1e-6 && Math.abs(r1.vel - 50) < 1e-6);

      const r2 = bounceValue(105, 100, 0, 100, 0.5);
      assert("Bounce right", Math.abs(r2.pos - 100) < 1e-6 && Math.abs(r2.vel + 50) < 1e-6);

      assert("Pinch hysteresis enter", hysteresis(false, 0.20, 0.30, 0.42) === true);
      assert("Pinch hysteresis hold", hysteresis(true, 0.36, 0.30, 0.42) === true);
      assert("Pinch hysteresis exit", hysteresis(true, 0.50, 0.30, 0.42) === false);

      const oe = new OneEuro();
      let val = 0;
      for (let i = 0; i < 20; i++) {
        val = oe.filter(Math.sin(i * 0.4) * 100, i * 16);
      }
      assert("One Euro finite", Number.isFinite(val));

      assert("Math helpers", clamp(2, 0, 1) === 1 && Math.abs(lerp(0, 10, 0.25) - 2.5) < 1e-6);

      const requiredEffects = ["aura", "orb", "throw", "lightning", "trail", "burst"];
      assert("Effects config complete", requiredEffects.every((k) => !!EFFECTS[k]));
    }

    function pickMimeType() {
      const types = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"];
      if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return "";
      for (const t of types) {
        if (MediaRecorder.isTypeSupported(t)) return t;
      }
      return "";
    }

    async function generateDemoVideo(seconds) {
      if (state.recording) return;

      if (!window.MediaRecorder || typeof canvas.captureStream !== "function") {
        setStatus("Video recording is not supported in this browser.");
        return;
      }

      unlockAudio();

      const stream = canvas.captureStream(30);
      let audioDest = null;

      if (audioCtx && masterGain && cfg.soundEnabled) {
        try {
          audioDest = audioCtx.createMediaStreamDestination();
          masterGain.connect(audioDest);
          const at = audioDest.stream.getAudioTracks()[0];
          if (at) stream.addTrack(at);
        } catch (e) {
          audioDest = null;
        }
      }

      const mime = pickMimeType();

      try {
        recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      } catch (e) {
        setStatus("Recorder failed: " + (e && e.message ? e.message : String(e)));
        return;
      }

      chunks = [];
      state.recording = true;
      btnRecord.disabled = true;
      btnRecord.textContent = "Recording...";

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());

        if (audioDest && masterGain) {
          try {
            masterGain.disconnect(audioDest);
          } catch (e) {}
        }

        const blob = new Blob(chunks, { type: recorder.mimeType || mime || "video/webm" });

        if (demoVideoUrl) URL.revokeObjectURL(demoVideoUrl);

        demoVideoUrl = URL.createObjectURL(blob);
        demoVideo.src = demoVideoUrl;
        demoVideo.style.display = "block";
        downloadLink.href = demoVideoUrl;
        downloadLink.style.display = "inline-block";

        setStatus("Local demo video generated. It stays in your browser.");

        state.recording = false;
        btnRecord.disabled = false;
        btnRecord.textContent = "Record local demo video";
      };

      recorder.start();

      window.setTimeout(() => {
        if (recorder && recorder.state !== "inactive") {
          recorder.stop();
        }
      }, Math.max(1, seconds) * 1000);
    }

    function resetSimulation() {
      for (const h of hands) resetHand(h);

      partAlive.fill(0);
      partLife.fill(0);
      particlePool.reset();

      orbActive.fill(0);
      orbLife.fill(0);
      orbPool.reset();

      recentEvents.length = 0;
      synthChecks = 0;
      synthCorrect = 0;
      latencyEMA = 0;
    }

    function deleteAllData() {
      if (recorder && recorder.state !== "inactive") {
        try {
          recorder.stop();
        } catch (e) {}
      }

      if (demoVideoUrl) {
        URL.revokeObjectURL(demoVideoUrl);
        demoVideoUrl = null;
      }

      demoVideo.removeAttribute("src");
      demoVideo.load();
      demoVideo.style.display = "none";

      downloadLink.href = "#";
      downloadLink.style.display = "none";

      chunks = [];

      disableCamera();
      resetSimulation();

      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch (e) {}

      setStatus("All local demo data deleted.");
    }

    function syncChip(el, on) {
      el.classList.toggle("on", !!on);
      el.classList.toggle("off", !on);
    }

    function updateChips() {
      syncChip(btnAura, cfg.effects.aura);
      syncChip(btnOrb, cfg.effects.orb);
      syncChip(btnThrow, cfg.effects.throw);
      syncChip(btnLightning, cfg.effects.lightning);
      syncChip(btnTrails, cfg.effects.trails);
      syncChip(btnBursts, cfg.effects.bursts);
      syncChip(btnSound, cfg.soundEnabled);
    }

    function setupUI() {
      btnCamera.addEventListener("click", () => {
        if (state.cameraOn) disableCamera();
        else enableCamera();
      });

      btnRecord.addEventListener("click", () => {
        generateDemoVideo(cfg.demoVideoSeconds);
      });

      btnDelete.addEventListener("click", () => {
        deleteAllData();
      });

      btnAura.addEventListener("click", () => {
        cfg.effects.aura = !cfg.effects.aura;
        updateChips();
      });

      btnOrb.addEventListener("click", () => {
        cfg.effects.orb = !cfg.effects.orb;
        updateChips();
      });

      btnThrow.addEventListener("click", () => {
        cfg.effects.throw = !cfg.effects.throw;
        updateChips();
      });

      btnLightning.addEventListener("click", () => {
        cfg.effects.lightning = !cfg.effects.lightning;
        updateChips();
      });

      btnTrails.addEventListener("click", () => {
        cfg.effects.trails = !cfg.effects.trails;
        updateChips();
      });

      btnBursts.addEventListener("click", () => {
        cfg.effects.bursts = !cfg.effects.bursts;
        updateChips();
      });

      btnSound.addEventListener("click", () => {
        cfg.soundEnabled = !cfg.soundEnabled;
        if (masterGain) masterGain.gain.value = cfg.soundEnabled ? cfg.maxVolume : 0;
        updateChips();
      });

      qualitySlider.value = String(cfg.quality);
      qualityValue.textContent = String(cfg.quality);

      qualitySlider.addEventListener("input", () => {
        cfg.quality = clamp(parseInt(qualitySlider.value, 10) || 3, 1, 5);
        effectiveQuality = cfg.quality;
        qualityValue.textContent = String(cfg.quality);
      });

      canvas.addEventListener("pointermove", (e) => {
        const r = canvas.getBoundingClientRect();
        pointer.x = clamp(((e.clientX - r.left) * W) / r.width, 0, W);
        pointer.y = clamp(((e.clientY - r.top) * H) / r.height, 0, H);

        if (!pointer.active) {
          pointer.px = pointer.x;
          pointer.py = pointer.y;
          pointer.active = true;
        }
      });

      canvas.addEventListener("pointerleave", () => {
        pointer.active = false;
      });

      canvas.addEventListener("pointerdown", (e) => {
        unlockAudio();
        const r = canvas.getBoundingClientRect();
        pointer.x = clamp(((e.clientX - r.left) * W) / r.width, 0, W);
        pointer.y = clamp(((e.clientY - r.top) * H) / r.height, 0, H);
        pointer.px = pointer.x;
        pointer.py = pointer.y;
        pointer.active = true;
      });

      window.addEventListener("pointerdown", unlockAudio, { passive: true });
    }

    async function init() {
      runTests();
      setupUI();
      updateChips();

      if (cfg.deleteNonce > 0) {
        deleteAllData();
      } else {
        setStatus(
          cfg.inputMode === "camera"
            ? "Press Enable camera to use webcam. Synthetic demo is running until then."
            : "Synthetic demo running. Click canvas to enable sound."
        );
      }

      requestAnimationFrame(tick);

      if (cfg.deleteNonce === 0 && cfg.autoDemoVideo && cfg.inputMode !== "camera") {
        window.setTimeout(() => {
          generateDemoVideo(cfg.demoVideoSeconds);
        }, 1200);
      }
    }

    init();
  </script>
</body>
</html>
"""


config = {
    "quality": int(quality),
    "soundEnabled": bool(sound),
    "maxVolume": float(max_volume),
    "autoDemoVideo": bool(auto_video and input_mode.startswith("Automatic") and delete_nonce == 0),
    "showLandmarks": bool(show_landmarks),
    "inputMode": "camera" if input_mode.startswith("Try") else "demo",
    "deleteNonce": int(delete_nonce),
    "mirrorCamera": True,
    "effects": {
        "aura": bool(aura),
        "orb": bool(orb),
        "throw": bool(throw),
        "lightning": bool(lightning),
        "trails": bool(trails),
        "bursts": bool(bursts),
    },
    "thresholds": {
        "pinchStart": float(pinch_start),
        "pinchEnd": float(pinch_end),
        "armHoldMs": int(arm_hold_ms),
        "refractoryMs": int(refractory_ms),
        "throwWindowMs": int(throw_window_ms),
        "throwGain": float(throw_gain),
        "throwMinSpeed": float(throw_min_speed),
        "throwMaxSpeed": float(throw_max_speed),
        "gravity": float(gravity),
        "damping": float(damping),
        "bounce": float(bounce),
        "lightningMaxPalmDist": float(lightning_dist),
    },
}

page = PAGE.replace("__MH_CONFIG__", json.dumps(config))

components.html(page, height=940, scrolling=False)

st.markdown("---")

st.markdown(
    """
    **Run command:** `python -m streamlit run app.py`  
    **Expected output:** browser opens, canvas starts immediately with synthetic hands, particles, orbs, lightning, HUD, event log, and a locally generated demo video appears below the canvas after a few seconds.  
    **Privacy:** no API key, no upload, camera only when enabled, delete-all-data control included.
    """
)