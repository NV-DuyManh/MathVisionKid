/** Retry keys identify one submission; they never carry authority or a reward. */
export function submissionId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const value = Math.floor(Math.random() * 16);
    return (c === 'x' ? value : (value & 3) | 8).toString(16);
  });
}
export function validQuizAnswer(value: string, unit: string): boolean {
  let text = value.trim().replace(/\s+/g, ' ');
  if (unit) for (const suffix of unit === 'quyển sách' ? ['quyển sách', 'quyển'] : [unit]) {
    if (text.toLocaleLowerCase('vi').endsWith(` ${suffix}`)) { text = text.slice(0, -suffix.length).trim(); break; }
  }
  return /^[+-]?\d{1,12}(?:\s*\/\s*0*[1-9]\d{0,11}|[.,]\d{1,8})?$/.test(text);
}
export function quizTime(milliseconds: number): string {
  const seconds = Number.isFinite(milliseconds) ? Math.max(0, Math.floor(milliseconds / 1000)) : 0;
  const minutes = Math.floor(seconds / 60), tail = String(seconds % 60).padStart(2, '0');
  return minutes < 60 ? `${minutes}:${tail}` : `${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, '0')}:${tail}`;
}
