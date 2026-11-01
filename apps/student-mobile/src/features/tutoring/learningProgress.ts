import { readLessonStorage, writeLessonStorage } from './lessonStorage';

export type LearningProgress={version:1;at:number;lessonId:string;sessionId:string;revision:number;stepIndex:number;problemText:string;workText:string;attempt:string;question?:string;reviewing?:boolean};
export function sameStoredAnswer(a:string,b:string):boolean{
  if(a===b)return true;
  const parse=(text:string)=>{const match=/^(-?)(\d{1,12})(?:[.,](\d{1,8}))?(?:\/(\d{1,12}))?$/.exec(text.trim());if(!match)return null;
    const denominator=BigInt(match[4]||'1')*BigInt(10)**BigInt((match[3]||'').length);if(!denominator)return null;
    return [BigInt((match[1]||'')+match[2]+(match[3]||'')),denominator];};
  const left=parse(a),right=parse(b);return !!left&&!!right&&left[0]*right[1]===right[0]*left[1];
}
const keyFor=(owner:string)=>`mathvision_progress_${Array.from(owner).map(c=>c.codePointAt(0)!.toString(16)).join('_')}`;
export function validLearningProgress(value:unknown):value is LearningProgress {
  const row=value as LearningProgress;
  return !!row&&row.version===1&&Number.isFinite(row.at)&&row.at<=Date.now()&&Date.now()-row.at<7*86400000
    &&typeof row.lessonId==='string'&&row.lessonId.length>0&&row.lessonId.length<=100
    &&typeof row.sessionId==='string'&&row.sessionId.length>=20&&row.sessionId.length<=100
    &&Number.isInteger(row.revision)&&row.revision>=0&&Number.isInteger(row.stepIndex)&&row.stepIndex>=0&&row.stepIndex<=10
    &&typeof row.problemText==='string'&&row.problemText.trim().length>=3&&row.problemText.length<=4000
    &&typeof row.workText==='string'&&row.workText.length<=6000&&typeof row.attempt==='string'&&row.attempt.length<=500
    &&(row.question===undefined||typeof row.question==='string'&&row.question.length<=500)&&(row.reviewing===undefined||typeof row.reviewing==='boolean');
}
export async function loadLearningProgress(owner?:string):Promise<LearningProgress|null>{
  if(!owner)return null;
  try{const parsed=JSON.parse(await readLessonStorage(keyFor(owner))||'null');return validLearningProgress(parsed)?parsed:null;}catch{return null;}
}
export async function saveLearningProgress(owner:string|undefined,row:LearningProgress):Promise<void>{
  if(!owner||!validLearningProgress(row))throw new Error('Chưa lưu được tiến độ.');
  await writeLessonStorage(keyFor(owner),JSON.stringify(row));
}
