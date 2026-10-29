import { readLessonStorage, writeLessonStorage } from './lessonStorage';

export function createPlaybackBookmarks(owner?: string) {
  const key = owner ? `mathvision_audio_${Array.from(owner).map(c=>c.codePointAt(0)!.toString(16)).join('_')}` : null;
  let entries: Record<string, { seconds: number; at: number }> = {};
  let timer: ReturnType<typeof setTimeout> | null = null;
  let dirty=false;
  const loaded = key ? readLessonStorage(key).then(raw => {
    const parsed = JSON.parse(raw || '{}');
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) entries = Object.fromEntries(Object.entries(parsed).filter(([id,value]) => {
      const item = value as { seconds: number; at: number };
      return id.length <= 10000 && item && Number.isFinite(item.seconds) && item.seconds>=0 && item.seconds<=240
        && Number.isFinite(item.at) && item.at<=Date.now() && Date.now()-item.at<86400000;
    }).slice(-20)) as typeof entries;
  }).catch(()=>{}) : Promise.resolve();
  const flush = () => {
    if (timer) clearTimeout(timer); timer=null;
    if(!key||!dirty)return Promise.resolve();dirty=false;
    return writeLessonStorage(key,JSON.stringify(entries)).catch(()=>{dirty=true;});
  };
  return {
    async get(id: string) { await loaded; return entries[id]?.seconds || 0; },
    set(id: string, seconds: number, duration: number) {
      if (!key || !Number.isFinite(seconds) || seconds<0 || seconds>240 || !Number.isFinite(duration) || duration<=0) return;
      const value = seconds >= duration-.3 ? 0 : Math.floor(seconds);
      if (entries[id]?.seconds===value) return;
      entries = { ...Object.fromEntries(Object.entries(entries).filter(([other])=>other!==id).slice(-19)), [id]: { seconds:value, at:Date.now() } };
      dirty=true;
      if (!timer) timer=setTimeout(()=>{void flush();},1000);
    },
    flush,
  };
}
