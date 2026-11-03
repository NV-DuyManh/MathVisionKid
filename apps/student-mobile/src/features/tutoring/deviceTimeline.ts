import { narrationChunks } from './narration';
import type { AudioCue } from './audioCues';

// Only speaking pace is retained, never pupil text/audio. Different system
// voices have different speeds; learn from complete readings in this app run.
const voicePace = new Map<string, number>();
export function estimatedDeviceDuration(voice: string, characters: number) {
  return characters * (voicePace.get(voice) ?? 1 / 12);
}
export function rememberDevicePace(voice: string, characters: number, seconds: number) {
  const pace = seconds / characters;
  if (!voice || characters < 40 || seconds < 2 || !Number.isFinite(pace) || pace < .02 || pace > 1) return;
  const prior = voicePace.get(voice);
  voicePace.delete(voice);
  voicePace.set(voice, prior === undefined ? pace : prior * .75 + pace * .25);
  if (voicePace.size > 8) voicePace.delete(voicePace.keys().next().value!);
}

/** Device speech exposes word positions, not a seekable audio file or measured duration. */
export function deviceTimeline(paragraphs: string[]) {
  let duration = 0;
  const cues: AudioCue[] = [];
  const chunks = paragraphs.flatMap((part, index) => {
    const start = duration;
    // Keep adjacent sentences in one utterance. Restarting the engine for every
    // sentence adds audible gaps and used to reset the visual clock repeatedly.
    const joined: string[] = [];
    for (const sentence of narrationChunks([part])) {
      const last = joined.length - 1;
      if (last >= 0 && joined[last].length + sentence.length < 420) joined[last] += ' ' + sentence;
      else joined.push(sentence);
    }
    const result = joined.map(text => {
      const start = duration;
      duration += text.length / 16;
      return { text, start, end: duration };
    });
    cues.push({ index, start, end: duration });
    return result;
  });
  return { chunks, cues, duration };
}

/** Seek anywhere on the estimated timeline, then restart from the nearest whole word. */
export function devicePosition(timeline: ReturnType<typeof deviceTimeline>, seconds: number) {
  const time = Number.isFinite(seconds) ? Math.max(0, Math.min(seconds, timeline.duration)) : 0;
  const index = timeline.chunks.findIndex(chunk => time < chunk.end);
  if (index < 0) return { index: timeline.chunks.length, offset: 0, time: timeline.duration };
  const chunk = timeline.chunks[index];
  let offset = Math.floor((time - chunk.start) / (chunk.end - chunk.start) * chunk.text.length);
  while (offset > 0 && !/\s/.test(chunk.text[offset - 1])) --offset;
  while (offset < chunk.text.length && /\s/.test(chunk.text[offset])) ++offset;
  return { index, offset, time: chunk.start + offset / 16 };
}

/** One elapsed clock for the entire reading, calibrated by actual engine events.
 * The engine supplies no audio duration. Extend the estimate instead of pinning
 * the clock at an invented per-sentence end. Only onDone confirms the total.
 */
export function deviceProgress(start: number, end: number, rate: number, now: number, initial = start, estimate = end) {
  const began = now, initialElapsed = end ? initial / end * estimate : 0;
  let frame = now, value = initial, elapsed = initialElapsed, duration = estimate, predicted = estimate, anchor = start;
  return {
    get elapsed() { return elapsed; },
    get duration() { return duration; },
    boundary(seconds: number, now: number) {
      const next = Math.max(anchor, Math.min(end, seconds)), spent = Math.max(0, (now - began) / 1000) * rate;
      if (next > anchor && spent > .3 && next > start) {
        predicted = initialElapsed + (end - start) * spent / (next - start);
      }
      anchor = next;
    },
    advance(now: number) {
      const delta = Math.max(0, (now - frame) / 1000); frame = now;
      elapsed = initialElapsed + Math.max(0, (now - began) / 1000) * rate;
      const correction = (predicted - duration) * (1 - Math.exp(-delta * 2));
      // Limit estimate growth so elapsed/duration continues forward while the
      // measured speaking pace corrects an initially short estimate.
      const growth = elapsed ? duration / elapsed * delta * rate * .8 : delta;
      duration = Math.max(elapsed + .75, duration + Math.max(-delta * rate, Math.min(growth, correction)));
      value = Math.max(value, Math.min(end - .0001, end * elapsed / duration));
      return value;
    },
    finish(now: number) {
      elapsed = initialElapsed + Math.max(0, (now - began) / 1000) * rate;
      return elapsed;
    },
  };
}
