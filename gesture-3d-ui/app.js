// app.js (V4)
// Touchless Control Suite — Gesture 3D UI (Tony Stark HUD)
// Right hand: rotate
// Left hand: pinch zoom
// Right fist: pause/resume
//
// Requirements:
// - index.html uses <script src=mediapipe UMD> for Hands + drawing_utils + camera_utils
// - app.js is ES module (type="module")
// - three.js loaded via CDN module imports

import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";

// -----------------------------
// DOM
// -----------------------------
const loadingEl = document.getElementById("loading");
const statusEl = document.getElementById("status");
const infoEl = document.getElementById("info");

const videoEl = document.getElementById("video");
const overlayCanvas = document.getElementById("overlay");
const overlayCtx = overlayCanvas.getContext("2d");

const threeCanvas = document.getElementById("three");

// -----------------------------
// Utils
// -----------------------------
const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const lerp = (a, b, t) => a + (b - a) * t;

function dist2(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.sqrt(dx * dx + dy * dy);
}

function nowMs() {
  return Date.now();
}

// -----------------------------
// State
// -----------------------------
let paused = false;

let lastFistToggle = 0;
const FIST_COOLDOWN_MS = 900;

let zoom = 3.2;
let targetZoom = 3.2;

const ZOOM_MIN = 1.8;
const ZOOM_MAX = 6.5;

// Rotation inertia
let rotX = 0;
let rotY = 0;

let targetRotX = 0;
let targetRotY = 0;

let prevRightPos = null;
let prevLeftPinch = null;

// Hand status
let rightDetected = false;
let leftDetected = false;

// -----------------------------
// Overlay sizing
// -----------------------------
function resize() {
  const w = window.innerWidth;
  const h = window.innerHeight;

  overlayCanvas.width = w;
  overlayCanvas.height = h;

  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);

// -----------------------------
// THREE.JS (V4 HUD)
// -----------------------------
const renderer = new THREE.WebGLRenderer({
  canvas: threeCanvas,
  antialias: true,
  alpha: true,
});

renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const scene = new THREE.Scene();

// Camera
const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100);
camera.position.set(0, 0, zoom);

// Lights
scene.add(new THREE.AmbientLight(0xffffff, 0.28));

const key = new THREE.DirectionalLight(0xffffff, 1.2);
key.position.set(3, 4, 6);
scene.add(key);

const rim = new THREE.DirectionalLight(0x00f5ff, 0.85);
rim.position.set(-5, 2, -4);
scene.add(rim);

// -----------------------------
// Background Grid (neon)
// -----------------------------
const grid = new THREE.GridHelper(30, 70, 0x00f5ff, 0x0a2b2e);
grid.position.y = -2.3;
grid.material.transparent = true;
grid.material.opacity = 0.22;
scene.add(grid);

// -----------------------------
// Center Orb (glass-ish)
// -----------------------------
const orbGeo = new THREE.IcosahedronGeometry(1.15, 3);
const orbMat = new THREE.MeshPhysicalMaterial({
  color: 0xffffff,
  metalness: 0.15,
  roughness: 0.06,
  transmission: 0.45,
  thickness: 1.0,
  clearcoat: 1.0,
  clearcoatRoughness: 0.06,
});
const orb = new THREE.Mesh(orbGeo, orbMat);
scene.add(orb);

// -----------------------------
// HUD Rings (3D)
// -----------------------------
function makeRing(inner, outer, opacity) {
  const g = new THREE.RingGeometry(inner, outer, 256);
  const m = new THREE.MeshBasicMaterial({
    color: 0x00f5ff,
    transparent: true,
    opacity,
    side: THREE.DoubleSide,
  });
  const r = new THREE.Mesh(g, m);
  r.rotation.x = Math.PI / 2;
  return r;
}

const ring1 = makeRing(1.35, 1.38, 0.22);
const ring2 = makeRing(1.55, 1.58, 0.14);
const ring3 = makeRing(1.80, 1.83, 0.10);

scene.add(ring1);
scene.add(ring2);
scene.add(ring3);

// -----------------------------
// Crosshair (HUD)
// -----------------------------
const crossGeo = new THREE.RingGeometry(0.03, 0.038, 64);
const crossMat = new THREE.MeshBasicMaterial({
  color: 0x00f5ff,
  transparent: true,
  opacity: 0.35,
  side: THREE.DoubleSide,
});
const cross = new THREE.Mesh(crossGeo, crossMat);
cross.position.set(0, 0, 0.2);
scene.add(cross);

// -----------------------------
// Particles (subtle)
// -----------------------------
const particleCount = 900;
const positions = new Float32Array(particleCount * 3);

for (let i = 0; i < particleCount; i++) {
  positions[i * 3 + 0] = (Math.random() - 0.5) * 18;
  positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
  positions[i * 3 + 2] = (Math.random() - 0.5) * 18;
}

const particlesGeo = new THREE.BufferGeometry();
particlesGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));

const particlesMat = new THREE.PointsMaterial({
  color: 0x00f5ff,
  size: 0.03,
  transparent: true,
  opacity: 0.25,
});

const particles = new THREE.Points(particlesGeo, particlesMat);
scene.add(particles);

// -----------------------------
// MediaPipe Hands (UMD global)
// -----------------------------
const hands = new Hands({
  locateFile: (file) =>
    `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

hands.setOptions({
  maxNumHands: 2,
  modelComplexity: 1,
  minDetectionConfidence: 0.65,
  minTrackingConfidence: 0.65,
});

// -----------------------------
// Gesture helpers
// -----------------------------
function handCenterX(hand, width) {
  // wrist(0) + middle mcp(9)
  const x = (hand[0].x + hand[9].x) / 2;
  return x * width;
}

function pinchDistance(hand) {
  // thumb tip(4) + index tip(8)
  return dist2(hand[4], hand[8]);
}

function isFist(hand) {
  // If finger tips are close to palm center -> fist
  const palm = {
    x: (hand[0].x + hand[9].x) / 2,
    y: (hand[0].y + hand[9].y) / 2,
  };

  const tips = [4, 8, 12, 16, 20].map((i) => hand[i]);
  let close = 0;

  for (const t of tips) {
    if (dist2(t, palm) < 0.18) close++;
  }

  return close >= 4;
}

// -----------------------------
// Minimal overlay (clean)
// -----------------------------
function drawMinimalOverlay(results) {
  overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

  if (!results.multiHandLandmarks) return;

  overlayCtx.save();
  overlayCtx.globalAlpha = 0.55;

  // small HUD label
  overlayCtx.font = "14px Arial";
  overlayCtx.fillStyle = "rgba(0,245,255,0.65)";
  overlayCtx.fillText("HAND TRACKING", 18, overlayCanvas.height - 22);

  // draw only fingertips
  const tips = [4, 8, 12, 16, 20];

  for (const hand of results.multiHandLandmarks) {
    for (const id of tips) {
      const lm = hand[id];
      const x = lm.x * overlayCanvas.width;
      const y = lm.y * overlayCanvas.height;

      overlayCtx.beginPath();
      overlayCtx.arc(x, y, 7, 0, Math.PI * 2);
      overlayCtx.fillStyle = "rgba(0,245,255,0.18)";
      overlayCtx.fill();

      overlayCtx.beginPath();
      overlayCtx.arc(x, y, 3, 0, Math.PI * 2);
      overlayCtx.fillStyle = "rgba(255,255,255,0.9)";
      overlayCtx.fill();
    }
  }

  overlayCtx.restore();
}

// -----------------------------
// UI update
// -----------------------------
function updateUI() {
  const mode = paused ? "PAUSED ✋" : "ACTIVE 🖐️";

  statusEl.textContent = mode;

  infoEl.textContent =
    `Right hand: ${rightDetected ? "Rotate ✅" : "not detected"}\n` +
    `Left hand: ${leftDetected ? "Zoom ✅" : "not detected"}\n` +
    `Zoom: ${zoom.toFixed(2)}\n` +
    `Gesture: Right = rotate | Left pinch = zoom | Right fist = pause`;
}

// -----------------------------
// Main gesture handler
// -----------------------------
function handleGestures(results) {
  rightDetected = false;
  leftDetected = false;

  if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
    prevRightPos = null;
    prevLeftPinch = null;
    updateUI();
    return;
  }

  // classify by x position (most reliable with mirrored camera)
  const w = overlayCanvas.width;

  const handsArr = results.multiHandLandmarks.map((h) => ({
    landmarks: h,
    cx: handCenterX(h, w),
  }));

  handsArr.sort((a, b) => a.cx - b.cx);

  const leftSide = handsArr[0]?.landmarks || null;
  const rightSide = handsArr[handsArr.length - 1]?.landmarks || null;

  // if only 1 hand -> treat as right control
  const rightHand = rightSide;
  const leftHand = handsArr.length >= 2 ? leftSide : null;

  rightDetected = !!rightHand;
  leftDetected = !!leftHand;

  // Pause toggle with right fist
  if (rightHand && isFist(rightHand)) {
    const t = nowMs();
    if (t - lastFistToggle > FIST_COOLDOWN_MS) {
      paused = !paused;
      lastFistToggle = t;

      // reset tracking memory
      prevRightPos = null;
      prevLeftPinch = null;
    }
  }

  if (paused) {
    updateUI();
    return;
  }

  // Right = rotate
  if (rightHand) {
    const idx = rightHand[8];

    if (!prevRightPos) {
      prevRightPos = { x: idx.x, y: idx.y };
    } else {
      const dx = idx.x - prevRightPos.x;
      const dy = idx.y - prevRightPos.y;

      // Inertia
      targetRotY += dx * 4.8;
      targetRotX += dy * 4.2;

      targetRotX = clamp(targetRotX, -1.45, 1.45);

      prevRightPos = { x: idx.x, y: idx.y };
    }
  }

  // Left = pinch zoom
  if (leftHand) {
    const p = pinchDistance(leftHand);

    if (prevLeftPinch === null) {
      prevLeftPinch = p;
    } else {
      const diff = p - prevLeftPinch;

      // diff > 0 => fingers open => zoom out
      // diff < 0 => pinch close => zoom in
      targetZoom += diff * 8.5;

      prevLeftPinch = p;
    }
  } else {
    prevLeftPinch = null;
  }

  targetZoom = clamp(targetZoom, ZOOM_MIN, ZOOM_MAX);

  updateUI();
}

// -----------------------------
// MediaPipe callback
// -----------------------------
hands.onResults((results) => {
  if (loadingEl && loadingEl.style.display !== "none") {
    loadingEl.style.display = "none";
  }

  drawMinimalOverlay(results);
  handleGestures(results);
});

// -----------------------------
// Camera start
// -----------------------------
async function startCamera() {
  const cam = new Camera(videoEl, {
    onFrame: async () => {
      await hands.send({ image: videoEl });
    },
    width: 1280,
    height: 720,
  });

  await cam.start();
}

// -----------------------------
// Animation loop
// -----------------------------
function animate() {
  requestAnimationFrame(animate);

  // Smooth rotation
  rotX = lerp(rotX, targetRotX, 0.12);
  rotY = lerp(rotY, targetRotY, 0.12);

  // Smooth zoom
  zoom = lerp(zoom, targetZoom, 0.14);
  camera.position.z = zoom;

  // Apply to objects
  orb.rotation.x = rotX;
  orb.rotation.y = rotY;

  // HUD animation
  ring1.rotation.z += 0.003;
  ring2.rotation.z -= 0.002;
  ring3.rotation.z += 0.0015;

  // subtle breathing
  const t = performance.now() * 0.001;
  orb.position.y = Math.sin(t * 1.2) * 0.04;

  // particles drift
  particles.rotation.y += 0.0007;

  renderer.render(scene, camera);
}
resize();
animate();

// -----------------------------
// Boot
// -----------------------------
(async function boot() {
  try {
    statusEl.textContent = "Loading...";
    infoEl.textContent = "Initializing camera & tracking...";

    await startCamera();

    statusEl.textContent = "ACTIVE 🖐️";
  } catch (err) {
    console.error(err);
    statusEl.textContent = "ERROR ❌";
    infoEl.textContent =
      "Camera failed. Use Live Server + allow camera.\n" + String(err);
  }
})();
