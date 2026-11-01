import { Platform } from 'react-native';
import { readLessonStorage, writeLessonStorage } from './lessonStorage';

type Sample = { at: number; stage: 'prepare' | 'transfer' | 'player'; ms: number; outcome: 'ready' | 'failed' | 'cancelled'; cache?: 'ready' | 'pending' | 'miss'; background?: boolean; voice: 'male' | 'female'; platform: string };
const KEY = 'mathvision_voice_metrics_v1';
let samples: Sample[] = [];
let initialization: Promise<void> | undefined;
const valid = (item: Sample) => item && Number.isFinite(item.at) && item.at <= Date.now() && Date.now()-item.at < 7*86400000
  && Number.isFinite(item.ms) && item.ms >= 0 && ['prepare','transfer','player'].includes(item.stage)
  && ['ready','failed','cancelled'].includes(item.outcome) && ['male','female'].includes(item.voice)
  && ['web','android','ios'].includes(item.platform)
  && (item.cache===undefined||['ready','pending','miss'].includes(item.cache))
  && (item.background===undefined||typeof item.background==='boolean');
function initialize() {
  initialization ??= readLessonStorage(KEY).then(raw => {
    const saved = JSON.parse(raw || '[]');
    if (Array.isArray(saved)) samples = [...saved.filter(valid).map(({at,stage,ms,outcome,cache,background,voice,platform}:Sample)=>({at,stage,ms,outcome,cache,background,voice,platform})), ...samples].slice(-200);
  }).catch(() => {});
  return initialization;
}
const clock = () => typeof performance !== 'undefined' ? performance.now() : Date.now();
export function measureVoice(stage: Sample['stage'], voice: string, context: Pick<Sample, 'cache' | 'background'> = {}) {
  void initialize();
  const started = clock(); let ended = false;
  return (outcome: Sample['outcome']) => {
    if (ended) return; ended = true;
    const sample: Sample = { at: Date.now(), stage, ms: Math.max(0, Math.round(clock()-started)), outcome, ...context,
      voice: voice.includes('HoaiMy') ? 'female' : 'male', platform: Platform.OS };
    samples = [...samples, sample].filter(item => Date.now()-item.at < 7*86400000).slice(-200);
    // Numerical diagnostics only. No pupil text, audio, identifiers, URLs or tokens.
    void initialize().then(()=>writeLessonStorage(KEY, JSON.stringify(samples))).catch(() => {});
  };
}
export async function voiceMetrics() {
  await initialize();
  const groups = [...new Set(samples.map(item => `${item.platform}:${item.stage}:${item.cache || 'network'}:${item.background ? 'background' : 'foreground'}`))];
  return { samples: [...samples], groups: groups.map(group => {
    const rows = samples.filter(item => `${item.platform}:${item.stage}:${item.cache || 'network'}:${item.background ? 'background' : 'foreground'}` === group);
    const ready = rows.filter(item => item.outcome === 'ready').map(item => item.ms).sort((a,b) => a-b);
    const percentile = (p: number) => ready.length ? ready[Math.max(0, Math.ceil(ready.length*p)-1)] : null;
    return { group, count: rows.length, failures: rows.filter(item => item.outcome === 'failed').length, cancelled: rows.filter(item => item.outcome === 'cancelled').length, p50: percentile(.5), p95: percentile(.95) };
  }) };
}
