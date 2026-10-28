import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useQuestionRecorder } from '../features/tutoring/useQuestionRecorder.web';

const getUserMedia = jest.fn(), stopTrack = jest.fn();
const construct = jest.fn();
let view: TestRenderer.ReactTestRenderer, recorder: ReturnType<typeof useQuestionRecorder>['recorder'];
const navigatorDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'navigator');
const mediaDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'MediaRecorder');
function Harness() { recorder = useQuestionRecorder().recorder; return null; }
beforeEach(() => {
  jest.clearAllMocks();
  getUserMedia.mockReset().mockResolvedValue({ getTracks: () => [{ stop: stopTrack }] });
  construct.mockReset();
  class MediaRecorderStub {
    static isTypeSupported() { return true; }
    state = 'inactive';
    constructor(stream: unknown, options: unknown) { construct(stream, options); }
  }
  Object.defineProperty(globalThis, 'navigator', { configurable: true, value: { mediaDevices: { getUserMedia } } });
  Object.defineProperty(globalThis, 'MediaRecorder', { configurable: true, value: MediaRecorderStub });
  act(() => { view = TestRenderer.create(<Harness />); });
});
afterEach(() => {
  act(() => view.unmount());
  if (navigatorDescriptor) Object.defineProperty(globalThis, 'navigator', navigatorDescriptor); else Reflect.deleteProperty(globalThis, 'navigator');
  if (mediaDescriptor) Object.defineProperty(globalThis, 'MediaRecorder', mediaDescriptor); else Reflect.deleteProperty(globalThis, 'MediaRecorder');
});

it('requests speech capture processing while retaining the existing recording bitrate', async () => {
  await act(async () => recorder.prepare());
  expect(getUserMedia).toHaveBeenCalledWith({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
  expect(construct).toHaveBeenCalledWith(expect.anything(), { mimeType: 'audio/webm;codecs=opus', audioBitsPerSecond: 64000 });
  await recorder.stop(); expect(stopTrack).toHaveBeenCalledTimes(1);
});

it('releases the microphone if constructing the browser recorder fails', async () => {
  construct.mockImplementationOnce(() => { throw new Error('Unsupported recorder'); });
  await expect(recorder.prepare()).rejects.toThrow('Unsupported recorder');
  expect(stopTrack).toHaveBeenCalledTimes(1);
});

it('releases tracks from a permission request resolved after dismissal', async () => {
  let finish!: (value: unknown) => void;
  getUserMedia.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const preparation = recorder.prepare(), rejected = expect(preparation).rejects.toThrow('Recording canceled');
  await recorder.stop(); finish({ getTracks: () => [{ stop: stopTrack }] }); await rejected;
  expect(stopTrack).toHaveBeenCalledTimes(1); expect(construct).not.toHaveBeenCalled();
});
