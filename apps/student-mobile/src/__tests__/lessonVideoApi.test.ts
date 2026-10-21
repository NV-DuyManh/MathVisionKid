import apiClient from '../services/api/apiClient';
import {lessonVideoApi} from '../features/tutoring/lessonVideoApi';
jest.mock('../services/api/apiClient',()=>({__esModule:true,default:{post:jest.fn()}}));
const ready={videoId:'v'.repeat(32),status:'READY',progress:100,durationSeconds:35,hasAudio:true,title:'Bài của em'};
beforeEach(()=>jest.clearAllMocks());
it('rejects silent ready responses and downloads only authenticated bounded MP4 bytes',async()=>{
 (apiClient.post as jest.Mock).mockResolvedValueOnce({data:{...ready,hasAudio:false}});
 await expect(lessonVideoApi.prepare({sessionId:'video-lesson-session-12345',revision:0})).rejects.toThrow();
 (apiClient.post as jest.Mock).mockResolvedValueOnce({data:new Uint8Array([0,0,0,24,102,116,121,112,105,115,111,109]).buffer});
 expect((await lessonVideoApi.download(ready.videoId)).length).toBe(12);
 expect(apiClient.post).toHaveBeenLastCalledWith('/student/tutor/lesson/video/content',{videoId:ready.videoId},expect.objectContaining({responseType:'arraybuffer'}));
 (apiClient.post as jest.Mock).mockResolvedValueOnce({data:new TextEncoder().encode('not a video').buffer});
 await expect(lessonVideoApi.download(ready.videoId)).rejects.toThrow();
});
