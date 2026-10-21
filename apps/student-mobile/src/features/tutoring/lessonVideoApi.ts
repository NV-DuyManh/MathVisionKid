import apiClient from '../../services/api/apiClient';

export type PersonalVideo = { videoId: string; status: 'RENDERING' | 'READY' | 'FAILED'; progress: number; durationSeconds: number; hasAudio: boolean; title: string };
const invalid = () => new Error('Chưa mở được video của bài này. Em thử lại nhé.');
const validId = (id: string) => /^[A-Za-z0-9_-]{24,64}$/.test(id);
function status(data: PersonalVideo, expectedId?: string): PersonalVideo {
  if (!data || typeof data.videoId !== 'string' || !validId(data.videoId) || (expectedId && data.videoId !== expectedId)
    || !['RENDERING','READY','FAILED'].includes(data.status) || !Number.isInteger(data.progress) || data.progress<0 || data.progress>100
    || !Number.isInteger(data.durationSeconds) || data.durationSeconds<0 || data.durationSeconds>242 || typeof data.hasAudio!=='boolean'
    || typeof data.title!=='string' || !data.title.trim() || data.title.length>220
    || (data.status==='READY' && (!data.hasAudio || data.durationSeconds===0 || data.progress!==100))) throw invalid();
  return data;
}
export const lessonVideoApi = {
  async prepare(request: {sessionId: string; revision: number}, signal?: AbortSignal): Promise<PersonalVideo> {
    if (!request || request.sessionId.length<20 || request.sessionId.length>100 || !Number.isInteger(request.revision) || request.revision<0) throw invalid();
    const {data}=await apiClient.post('/student/tutor/lesson/video',request,{signal,timeout:15000});return status(data);
  },
  async status(videoId: string, signal?: AbortSignal): Promise<PersonalVideo> {
    if (!validId(videoId)) throw invalid();
    const {data}=await apiClient.post('/student/tutor/lesson/video/status',{videoId},{signal,timeout:15000});return status(data,videoId);
  },
  async download(videoId: string, signal?: AbortSignal): Promise<Uint8Array> {
    if (!validId(videoId)) throw invalid();
    const {data}=await apiClient.post('/student/tutor/lesson/video/content',{videoId},{signal,timeout:45000,responseType:'arraybuffer',headers:{Accept:'video/mp4'}});
    const bytes=new Uint8Array(data);
    if (bytes.length<12 || bytes.length>16*1024*1024 || bytes[4]!==102 || bytes[5]!==116 || bytes[6]!==121 || bytes[7]!==112) throw invalid();
    return bytes;
  },
};
