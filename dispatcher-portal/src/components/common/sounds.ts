// ─── NOTIFICATION CHIMES (Web Audio API) ─────────────────────────
// Dispatcher portal event tone (wav)
// Using a generic chime instead of an actual WAV file to avoid missing asset errors,
// since the asset './car_honk_3s_opt1_cluster.wav' is not provided.

const playChime = (notes: {freq: number, start: number, dur: number}[]) => {
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) return;
    const ctx = new AudioContextClass();
    const now = ctx.currentTime;
    notes.forEach(({ freq, start, dur }) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.18, now + start);
      gain.gain.exponentialRampToValueAtTime(0.001, now + start + dur);
      osc.connect(gain).connect(ctx.destination);
      osc.start(now + start);
      osc.stop(now + start + dur + 0.05);
    });
    setTimeout(() => ctx.close(), 1500);
  } catch (e) { console.warn('[Chime] Could not play:', e); }
};

// New order: loud alert chime
export const playNewOrderChime = () => playChime([
  { freq: 440, start: 0, dur: 0.2 },
  { freq: 440, start: 0.2, dur: 0.2 },
  { freq: 440, start: 0.4, dur: 0.2 },
  { freq: 523, start: 0.6, dur: 0.4 },
]);

// Started: subtle chime
export const playStartedChime = () => playChime([
  { freq: 523, start: 0, dur: 0.12 },    // C5
  { freq: 659, start: 0.12, dur: 0.2 },  // E5
]);

// Delivered: success chime
export const playDeliveredChime = () => playChime([
  { freq: 659, start: 0, dur: 0.1 },     // E5
  { freq: 784, start: 0.1, dur: 0.1 },   // G5
  { freq: 1047, start: 0.2, dur: 0.3 },  // C6
]);
