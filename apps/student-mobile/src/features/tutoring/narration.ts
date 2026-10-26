import type { CompletedLessonStep, LessonStep } from './api/TutorService';
import type { Voice } from 'expo-speech';

/** Only fields already opened by the lesson service; never serialize the step. */
export function stepNarration(step: LessonStep, hint = ''): string[] {
  return unique([step.explanation, ...(step.guidance || []), hint, step.question]);
}

export function completedNarration(steps: CompletedLessonStep[]): string[] {
  return steps.flatMap(step => unique([step.solutionSentence || step.title,
    step.expression ? `${step.expression} = ${step.answer}${step.unit ? ` (${step.unit})` : ''}` : step.answer,
    step.explanation, ...(step.guidance || []), ...(step.calculationDetails || [])]));
}

function unique(parts: string[]): string[] {
  return [...new Set(parts.map(part => part.trim()).filter(Boolean))];
}

/** Pronunciation only: do not evaluate, simplify, or invent a calculation. */
export function spokenMath(text: string): string {
  return text
    .replace(/\(([\d.,+\-−×*÷:\s]+)\)\s*\/\s*\(([\d.,+\-−×*÷:\s]+)\)/g,
      (_, top, bottom) => /^[-+]?\d+(?:[.,]\d+)?$/.test(top.trim()) && /^[-+]?\d+(?:[.,]\d+)?$/.test(bottom.trim())
        ? ` ${top} phần ${bottom} ` : ` phân số có tử số là ${top}, và mẫu số là ${bottom} `)
    .replace(/(?<![\d/])(\d+(?:[.,]\d+)?)\s*\/\s*(\d+(?:[.,]\d+)?)(?![\d/])/g, '$1 phần $2')
    .replace(/(^|[=(:,+*×÷/\-−]\s*)[-−]\s*(?=\d)/g, '$1âm ')
    .replace(/[×*]/g, ' nhân ')
    .replace(/(\d|\))\s*x\s*(?=[(\d])/g, '$1 nhân ')
    .replace(/(\d|\))\s*[:÷]\s*(?=[(\d])/g, '$1 chia ')
    .replace(/(^|[=(,:]\s*)[-−]\s*(?=\d)/g, '$1âm ')
    .replace(/[-−](?=\s*\d)/g, ' trừ ')
    .replace(/\+/g, ' cộng ').replace(/=/g, ' bằng ')
    .replace(/\((\s*[\p{L}²³]+\s*)\)/gu, ' $1 ')
    .replace(/(?<![\p{L}])(km|dm|cm|mm|kg|mg|ml|m|g|l)([²³])?(?![\p{L}])/gu, (_, unit: string, power?: string) =>
      ` ${({ km: 'ki lô mét', dm: 'đề xi mét', cm: 'xăng ti mét', mm: 'mi li mét', m: 'mét',
        kg: 'ki lô gam', mg: 'mi li gam', g: 'gam', ml: 'mi li lít', l: 'lít' } as Record<string, string>)[unit]}${power ? power === '²' ? ' vuông' : ' khối' : ''} `)
    .replace(/%/g, ' phần trăm ').replace(/\(/g, ' mở ngoặc ').replace(/\)/g, ' đóng ngoặc ').replace(/\s+/g, ' ').trim();
}

/** Small utterances avoid platform length limits and provide natural pauses. */
export function narrationChunks(parts: string[]): string[] {
  return parts.flatMap(part => {
    const sentences = spokenMath(part).split(/(?<=[.!?])\s+/);
    return sentences.flatMap(sentence => {
      const chunks: string[] = []; let chunk = '';
      for (const word of sentence.split(/\s+/)) {
        if (chunk && chunk.length + word.length > 420) { chunks.push(chunk); chunk = ''; }
        chunk += (chunk ? ' ' : '') + word;
      }
      if (chunk) chunks.push(chunk);
      return chunks;
    });
  }).filter(Boolean);
}

/** A short opening starts quickly; following clips are warmed while it plays. */
export function narrationSegments(parts: string[]): string[] {
  const segments: string[] = [];
  for (const word of narrationChunks(parts).flatMap(chunk => chunk.split(/\s+/))) {
    const last = segments.length - 1;
    const limit = last === 0 ? 160 : 420;
    if (last >= 0 && segments[last].length + word.length + 1 <= limit) segments[last] += ` ${word}`;
    else segments.push(word);
  }
  return segments;
}

export function vietnameseVoices(voices: Voice[]): Voice[] {
  const seen = new Set<string>();
  const score = (v: Voice) => (v.quality === 'Enhanced' ? 8 : 0)
    + (/natural|hoaimy|namminh/i.test(v.name.replace(/\s/g, '')) ? 4 : 0)
    + (v.language.toLowerCase().replace('_', '-') === 'vi-vn' ? 2 : 0);
  return voices.filter(v => /^vi(?:[-_]|$)/i.test(v.language) && !!v.identifier
    && !seen.has(v.identifier) && !!seen.add(v.identifier)).sort((a, b) => score(b) - score(a)).slice(0, 2);
}

export function voiceLabel(voice: Voice, index: number): string {
  const name = voice.name.normalize('NFD').replace(/[\u0300-\u036f\s]/g, '').toLowerCase();
  return name.includes('hoaimy') ? 'Hoài My' : name.includes('namminh') ? 'Nam Minh' : `Giọng Việt ${index + 1}`;
}
