import apiClient from '../services/api/apiClient';
import { quizApi } from '../features/quiz/quizApi';

jest.mock('../services/api/apiClient',()=>({__esModule:true,default:{post:jest.fn()}}));
const voice='vi-VN-HoaiMyNeural';
const wav=new Uint8Array(50);wav.set([82,73,70,70]);wav.set([87,65,86,69],8);
beforeEach(()=>{jest.useFakeTimers();(apiClient.post as jest.Mock).mockReset();});
afterEach(()=>jest.useRealTimers());

it('retries a transient failure with the exact same voice and authorized content inside one deadline',async()=>{
  (apiClient.post as jest.Mock).mockRejectedValueOnce({response:{status:429}}).mockResolvedValueOnce({data:wav.buffer});
  const signal=new AbortController().signal;
  const result=quizApi.audio('owned-quiz',voice,signal,'QUESTION');
  await jest.advanceTimersByTimeAsync(500);
  expect(await result).toEqual(wav);
  const calls=(apiClient.post as jest.Mock).mock.calls;
  expect(calls).toHaveLength(2);
  expect(calls.map(call=>call[1])).toEqual([{voice,content:'QUESTION'},{voice,content:'QUESTION'}]);
  expect(calls[0][2]).toEqual(expect.objectContaining({signal,timeout:60000}));
  expect(calls[1][2].timeout).toBe(59500);
});

it.each([401,403,404,409,410,422])('never retries authorization or stale-content failure %s',async(status)=>{
  const error={response:{status}};(apiClient.post as jest.Mock).mockRejectedValue(error);
  await expect(quizApi.audio('owned-quiz',voice,new AbortController().signal,'SOLUTION')).rejects.toBe(error);
  expect(apiClient.post).toHaveBeenCalledTimes(1);
});

it('stops retries after two transient retries instead of restarting the sixty-second budget',async()=>{
  const error={response:{status:503}};(apiClient.post as jest.Mock).mockRejectedValue(error);
  const result=expect(quizApi.audio('owned-quiz',voice,new AbortController().signal)).rejects.toBe(error);
  await jest.advanceTimersByTimeAsync(2000);await result;
  expect(apiClient.post).toHaveBeenCalledTimes(3);
});

it('waits for shared provider capacity through busy responses without failing after only two retries',async()=>{
  (apiClient.post as jest.Mock).mockRejectedValueOnce({response:{status:429}})
    .mockRejectedValueOnce({response:{status:429}}).mockRejectedValueOnce({response:{status:429}})
    .mockResolvedValueOnce({data:wav.buffer});
  const result=quizApi.audio('owned-quiz',voice,new AbortController().signal);
  await jest.advanceTimersByTimeAsync(3000);
  expect(await result).toEqual(wav);
  expect(apiClient.post).toHaveBeenCalledTimes(4);
  expect((apiClient.post as jest.Mock).mock.calls[3][2].timeout).toBe(57000);
});

it('stops sustained capacity errors at the original sixty-second deadline',async()=>{
  const busy={response:{status:429}};(apiClient.post as jest.Mock).mockRejectedValue(busy);
  const result=expect(quizApi.audio('owned-quiz',voice,new AbortController().signal)).rejects.toBe(busy);
  await jest.advanceTimersByTimeAsync(60000);await result;
  const calls=(apiClient.post as jest.Mock).mock.calls;
  expect(calls.length).toBeGreaterThan(3);
  expect(calls.length).toBeLessThan(40);
  expect(calls.every(call=>call[2].timeout>0&&call[2].timeout<=60000)).toBe(true);
});

it('does not start another request after a failure consumes the remaining deadline',async()=>{
  const error={response:{status:503}};
  (apiClient.post as jest.Mock).mockImplementation(async()=>{jest.advanceTimersByTime(59900);throw error;});
  await expect(quizApi.audio('owned-quiz',voice,new AbortController().signal)).rejects.toBe(error);
  expect(apiClient.post).toHaveBeenCalledTimes(1);
});

it('aborting a retry wait cancels it without a late request',async()=>{
  (apiClient.post as jest.Mock).mockRejectedValue({code:'ERR_NETWORK'});
  const controller=new AbortController();
  const result=expect(quizApi.audio('owned-quiz',voice,controller.signal)).rejects.toThrow('Đã dừng');
  await jest.advanceTimersByTimeAsync(100);controller.abort();await result;
  await jest.advanceTimersByTimeAsync(2000);
  expect(apiClient.post).toHaveBeenCalledTimes(1);
});

it('does not retry or publish an invalid WAV response',async()=>{
  (apiClient.post as jest.Mock).mockResolvedValue({data:new ArrayBuffer(2)});
  await expect(quizApi.audio('owned-quiz',voice,new AbortController().signal)).rejects.toThrow('Invalid audio');
  expect(apiClient.post).toHaveBeenCalledTimes(1);
});
