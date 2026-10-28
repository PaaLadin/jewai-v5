
let audioCtx = null;
function initAudio() {
    if (!audioCtx) {
        try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch(e) {}
    }
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
}
function playNoise(duration, filterFreq, gainVal, q) {
    if (!audioCtx) return;
    let bufferSize = audioCtx.sampleRate * duration;
    let buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
    let data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
    let noise = audioCtx.createBufferSource();
    noise.buffer = buffer;
    let filter = audioCtx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = filterFreq;
    filter.Q.value = q || 1;
    let gain = audioCtx.createGain();
    gain.gain.setValueAtTime(gainVal, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration);
    noise.connect(filter);
    filter.connect(gain);
    gain.connect(audioCtx.destination);
    noise.start();
}
function sfxKey() { playNoise(0.04, 2000, 0.4, 5); }
function sfxEnter() { playNoise(0.1, 400, 0.6, 2); }
function sfxType() { playNoise(0.02, 3000, 0.3, 8); }
function sfxDisk() { playNoise(0.15, 600, 0.4, 3); setTimeout(() => playNoise(0.1, 800, 0.3, 3), 150); setTimeout(() => playNoise(0.2, 500, 0.4, 3), 300); }

function sfxCoinDrop() { if (!audioCtx) return; const now = audioCtx.currentTime; let t = audioCtx.createOscillator(); let tg = audioCtx.createGain(); t.type = 'sine'; t.frequency.setValueAtTime(120, now); t.frequency.exponentialRampToValueAtTime(40, now + 0.05); tg.gain.setValueAtTime(0.6, now); tg.gain.exponentialRampToValueAtTime(0.01, now + 0.05); t.connect(tg); tg.connect(audioCtx.destination); t.start(now); t.stop(now + 0.05); let p = audioCtx.createOscillator(); let pg = audioCtx.createGain(); p.type = 'triangle'; let f = 3000 + (Math.random() * 1000); p.frequency.setValueAtTime(f, now); p.frequency.exponentialRampToValueAtTime(f * 0.9, now + 0.08); pg.gain.setValueAtTime(0.3, now); pg.gain.exponentialRampToValueAtTime(0.001, now + 0.12); p.connect(pg); pg.connect(audioCtx.destination); p.start(now); p.stop(now + 0.12); }
function sfxCoins(duration) { if (!audioCtx) return; for (let i = 0; i < 15; i++) { let delay = (i / 15) * duration + (Math.random() * 0.05); setTimeout(() => sfxCoinDrop(), delay * 1000); } }

function playWebMoneyCoins() {
    if (!audioCtx) return;
    const now = audioCtx.currentTime;
    const masterGain = audioCtx.createGain();
    masterGain.gain.setValueAtTime(1.2, now);
    const limiter = audioCtx.createDynamicsCompressor();
    limiter.threshold.setValueAtTime(-2, now);
    limiter.knee.setValueAtTime(0, now);
    limiter.ratio.setValueAtTime(20, now);
    limiter.attack.setValueAtTime(0.001, now);
    limiter.release.setValueAtTime(0.04, now);
    const globalFilter = audioCtx.createBiquadFilter();
    globalFilter.type = 'lowpass';
    globalFilter.frequency.setValueAtTime(8500, now);
    masterGain.connect(limiter); limiter.connect(globalFilter); globalFilter.connect(audioCtx.destination);

    function triggerHit(time, volume, duration, metalFreq) {
        const bs = audioCtx.sampleRate * 0.04;
        const buf = audioCtx.createBuffer(1, bs, audioCtx.sampleRate);
        const data = buf.getChannelData(0);
        for (let i = 0; i < bs; i++) data[i] = Math.random() * 2 - 1;
        const wood = audioCtx.createBufferSource(); wood.buffer = buf;
        const wf = audioCtx.createBiquadFilter(); wf.type = 'bandpass'; wf.frequency.setValueAtTime(450, time); wf.Q.setValueAtTime(5, time);
        const wg = audioCtx.createGain(); wg.gain.setValueAtTime(volume * 1.3, time); wg.gain.exponentialRampToValueAtTime(0.001, time + 0.012);
        wood.connect(wf); wf.connect(wg); wg.connect(masterGain);
        const metal = audioCtx.createBufferSource(); metal.buffer = buf;
        const mf = audioCtx.createBiquadFilter(); mf.type = 'bandpass'; mf.frequency.setValueAtTime(metalFreq, time); mf.Q.setValueAtTime(20, time);
        const mg = audioCtx.createGain(); mg.gain.setValueAtTime(volume * 0.85, time); mg.gain.exponentialRampToValueAtTime(0.001, time + duration);
        metal.connect(mf); mf.connect(mg); mg.connect(masterGain);
        const chirp = audioCtx.createOscillator(); const cg = audioCtx.createGain(); chirp.type = 'sine';
        const cf = 3200 + (metalFreq - 1500) * 0.8; chirp.frequency.setValueAtTime(cf, time);
        cg.gain.setValueAtTime(volume * 0.4, time); cg.gain.exponentialRampToValueAtTime(0.001, time + 0.008);
        chirp.connect(cg); cg.connect(masterGain);
        wood.start(time); metal.start(time); chirp.start(time);
        wood.stop(time + 0.02); metal.stop(time + duration + 0.01); chirp.stop(time + 0.015);
    }

    const layers = [
        { metalFreq: 1650, startTime: 0.0, speed: 0.89, initialInterval: 0.26, count: 17 },
        { metalFreq: 1480, startTime: 0.10, speed: 0.87, initialInterval: 0.30, count: 14 },
        { metalFreq: 1850, startTime: 0.30, speed: 0.91, initialInterval: 0.20, count: 22 },
        { metalFreq: 1350, startTime: 0.55, speed: 0.85, initialInterval: 0.35, count: 12 }
    ];

    layers.forEach(layer => {
        let elapsedTime = layer.startTime;
        let currentInterval = layer.initialInterval;
        for (let i = 0; i < layer.count; i++) {
            const hitTime = now + elapsedTime;
            const progress = elapsedTime / 3.5;
            if (progress > 1) break;
            const volume = Math.max(0.02, (1 - progress * 0.75) * 0.65);
            const hitDuration = Math.max(0.018, currentInterval * 0.5);
            const jitterFreq = layer.metalFreq + (Math.sin(i * 3) * 60);
            triggerHit(hitTime, volume, hitDuration, jitterFreq);
            elapsedTime += currentInterval;
            currentInterval *= layer.speed;
            if (currentInterval < 0.012) currentInterval = 0.012;
        }
    });
}
