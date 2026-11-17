const input = document.getElementById("video");
const title = document.getElementById("fileTitle");
const hint = document.getElementById("fileHint");
const zone = document.getElementById("dropzone");
const qualityRow = document.getElementById("qualityRow");

input.addEventListener("change", () => {
  if (input.files.length) {
    title.textContent = input.files[0].name;
    hint.textContent = `${(input.files[0].size / 1024 / 1024).toFixed(1)} MB · พร้อมแปลง`;
  }
});
["dragenter","dragover"].forEach(event => zone.addEventListener(event, e => {
  e.preventDefault(); zone.classList.add("drag");
}));
["dragleave","drop"].forEach(event => zone.addEventListener(event, e => {
  e.preventDefault(); zone.classList.remove("drag");
}));
zone.addEventListener("drop", e => {
  if (e.dataTransfer.files.length) {
    input.files = e.dataTransfer.files;
    input.dispatchEvent(new Event("change"));
  }
});
document.querySelectorAll('input[name="format"]').forEach(radio => {
  radio.addEventListener("change", () => {
    qualityRow.style.opacity = radio.value === "mp3" && radio.checked ? ".35" : "1";
    document.getElementById("quality").disabled = radio.value === "mp3" && radio.checked;
  });
});

// Lightweight animated star particles, with reduced-motion support.
const canvas = document.getElementById("stars");
const ctx = canvas.getContext("2d");
let width, height, stars = [], raf;
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  width = window.innerWidth; height = window.innerHeight;
  canvas.width = width * dpr; canvas.height = height * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  stars = Array.from({length: Math.min(110, Math.floor(width * height / 8500))}, () => ({
    x: Math.random()*width, y: Math.random()*height,
    r: Math.random()*1.35+.25, a: Math.random()*.65+.15,
    speed: Math.random()*.22+.035, phase: Math.random()*Math.PI*2
  }));
}
function draw(t=0) {
  ctx.clearRect(0,0,width,height);
  for (const s of stars) {
    const pulse = reduceMotion ? 1 : .65 + .35*Math.sin(t*.001*s.speed*5+s.phase);
    ctx.beginPath(); ctx.arc(s.x,s.y,s.r,0,Math.PI*2);
    ctx.fillStyle = `rgba(218,224,255,${s.a*pulse})`; ctx.fill();
    if (!reduceMotion) { s.y -= s.speed*.22; if(s.y < -3){s.y=height+3;s.x=Math.random()*width;} }
  }
  if (!reduceMotion) raf = requestAnimationFrame(draw);
}
window.addEventListener("resize", resize);
resize(); draw();
