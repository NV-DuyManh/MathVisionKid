import type { CompletedLessonStep, LessonStep } from './api/TutorService';
import type { Voice } from 'expo-speech';

export const NARRATION_PROGRESS_STEPS = ['Giọng đọc đã chọn', 'Chuẩn bị âm thanh', 'Mở lời giảng'] as const;

/** Only fields already opened by the lesson service; never serialize the step. */
export function stepNarration(step: LessonStep, hint = ''): string[] {
  return unique([...(step.guidance?.length ? step.guidance : [step.explanation]), hint, step.question]);
}

export function completedNarration(steps: CompletedLessonStep[]): string[] {
  return steps.flatMap(step => unique([step.solutionSentence || step.title,
    step.expression ? `${step.expression} = ${step.answer}${step.unit ? ` (${step.unit})` : ''}` : step.answer,
    ...(steps.length === 1 ? [step.explanation] : [])]));
}

function unique(parts: string[]): string[] {
  return [...new Set(parts.map(part => part.trim()).filter(Boolean))];
}

/** Pronunciation only: do not evaluate, simplify, or invent a calculation. */
export function spokenMath(text: string): string {
  return text
    .replace(/(?<![\p{L}_])(km|dm|cm|mm|m)(?:\^\{([23])\}|\^?([23]))(?![\p{L}\p{N}_])/gu,
      (_, unit: string, brace: string, plain: string) => unit + ({ '2': '²', '3': '³' } as Record<string, string>)[brace || plain])
    .replace(/\b((?:Bài|Câu)\s+\d+)\s*[:.)]\s*/gi, '$1. ')
    .replace(/(?<![\p{L}])(?:đề|đê|xăng|ki|mi)[\s\-‐‑–]+(?:xi|ti|lô|li)[\s\-‐‑–]+(?:mét|gam|lít)(?![\p{L}])/giu,
      unit => unit.replace(/[-‐‑–]/g, ' '))
    .replace(/\s*\(\s*\d+(?:[.,]\d+)?\s*điểm\s*\)\s*,?\s*/gi, ' ')
    .replace(/\b((?:Bài|Câu)\s+\d+)\.\s*\./gi, '$1.')
    .replace(/\(\s*((?:ki lô|đề xi|xăng ti|mi li)?\s*(?:mét|gam|lít)(?:\s+(?:vuông|khối))?)\s*\)/gi, ' $1 ')
    .replace(/\(([\d.,+\-−×*÷:\s]+)\)\s*\/\s*\(([\d.,+\-−×*÷:\s]+)\)/g,
      (_, top, bottom) => /^[-+]?\d+(?:[.,]\d+)?$/.test(top.trim()) && /^[-+]?\d+(?:[.,]\d+)?$/.test(bottom.trim())
        ? ` ${top} phần ${bottom} ` : ` phân số có tử số là ${top}, và mẫu số là ${bottom} `)
    .replace(/(?<![\d/])(\d+(?:[.,]\d+)?)\s*\/\s*(\d+(?:[.,]\d+)?)(?![\d/])/g, '$1 phần $2')
    .replace(/(^|[=(:,+*×÷/\-−]\s*)[-−]\s*(?=\d)/g, '$1âm ')
    .replace(/[×*]/g, ' nhân ')
    .replace(/(\d|\))\s*x\s*(?=[(\d])/g, '$1 nhân ')
    .replace(/(\d|\))\s*[:÷]\s*(?=[(\d]|âm\s+\d)/g, '$1 chia ')
    .replace(/[-−](?=\s*\d)/g, ' trừ ')
    .replace(/\+/g, ' cộng ').replace(/=/g, ' bằng ')
    .replace(/\(\s*((?:km|dm|cm|mm|kg|mg|ml|m|g|l)(?:[²³])?)\s*\)/g, ' $1 ')
    .replace(/(?<![\p{L}_])(km|dm|cm|mm|kg|mg|ml|m|g|l)([²³])?(?![\p{L}\p{N}_])/gu, (_, unit: string, power?: string) =>
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
  return name.includes('hoaimy') ? 'Giọng nữ' : name.includes('namminh') ? 'Giọng nam' : `Giọng Việt ${index + 1}`;
}
