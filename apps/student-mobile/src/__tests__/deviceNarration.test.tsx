import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { DeviceNarration } from '../features/tutoring/DeviceNarration';
import { AppState } from 'react-native';
import { MediaTimeline } from '../features/tutoring/MediaTimeline';
import { devicePosition, deviceProgress, deviceTimeline, estimatedDeviceDuration, rememberDevicePace } from '../features/tutoring/deviceTimeline';
import { preparePlaybackSession } from '../features/tutoring/playbackSession';
import { getAvailableVoicesAsync, speak, stop } from '../features/tutoring/speechOutput';
jest.mock('../features/tutoring/speechOutput', () => ({ getAvailableVoicesAsync: jest.fn(), speak: jest.fn(), stop: jest.fn().mockResolvedValue(undefined) }));
jest.mock('../features/tutoring/playbackSession', () => ({ preparePlaybackSession: jest.fn().mockResolvedValue(undefined) }));
const mockNavigation = { addListener: jest.fn(() => jest.fn()) };
jest.mock('expo-router', () => ({ useNavigation: () => mockNavigation }));
let view: TestRenderer.ReactTestRenderer;
beforeEach(() => {
  jest.clearAllMocks();
  (getAvailableVoicesAsync as jest.Mock).mockResolvedValue([{ identifier: 'vi-test', language: 'vi-VN', name: 'Vietnamese', quality: 'Default' }]);
});
afterEach(() => { act(() => view?.unmount()); jest.restoreAllMocks(); jest.useRealTimers(); });
const player = () => view.root.findByType(MediaTimeline);
const render = async (onFinished = jest.fn()) => {
  await act(async () => { view = TestRenderer.create(<DeviceNarration paragraphs={['Em cộng 1/3 với 2/5.']} onFinished={onFinished} />); });
};
it('uses a Vietnamese device voice only on a click and stops on close', async () => {
  const done = jest.fn(); await render(done);
  expect(speak).not.toHaveBeenCalled();
  await act(async () => player().props.onToggle());
  expect(speak).toHaveBeenCalledWith(expect.stringContaining('1 phần 3'), expect.objectContaining({ voice: 'vi-test' }));
  const callbacks = (speak as jest.Mock).mock.calls[0][1];
  act(() => callbacks.onStart()); act(() => callbacks.onDone()); expect(done).toHaveBeenCalledTimes(1);
  act(() => view.unmount()); expect(stop).toHaveBeenCalled();
});
it('ignores completion from a stopped reading without cancelling the new watchdog', async () => {
  jest.useFakeTimers(); await render();
  await act(async () => player().props.onToggle());
  const old=(speak as jest.Mock).mock.calls[0][1];
  await act(async () => player().props.onToggle());
  await act(async () => player().props.onToggle());
  act(() => old.onDone());
  act(() => jest.advanceTimersByTime(8000));
  const words=view.root.findAllByType('Text' as any).map(n=>String(n.props.children)).join(' ');
  expect(words).toContain('Giọng thiết bị chưa phát được');
});
it('does not substitute English when the device has no Vietnamese voice', async () => {
  (getAvailableVoicesAsync as jest.Mock).mockResolvedValue([{ identifier: 'en', language: 'en-US', name: 'English' }]);
  await render(); expect(view.root.findAllByType(MediaTimeline)).toHaveLength(0); expect(speak).not.toHaveBeenCalled();
});
it('reports a device engine that never starts instead of hanging', async () => {
  jest.useFakeTimers(); await render();
  await act(async () => player().props.onToggle());
  act(() => jest.advanceTimersByTime(8000));
  const words = view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ');
  expect(words).toContain('Giọng thiết bị chưa phát được'); expect(stop).toHaveBeenCalled();
});

it('can check device voices again without speaking automatically or substituting English', async () => {
  (getAvailableVoicesAsync as jest.Mock).mockResolvedValueOnce([]);
  await render();
  const retry=view.root.findAll(node=>node.props.accessibilityLabel==='Thử lại giọng thiết bị'&&node.props.onPress)[0];
  await act(async()=>retry.props.onPress());
  expect(getAvailableVoicesAsync).toHaveBeenCalledTimes(2);
  expect(speak).not.toHaveBeenCalled();
  expect(player().props.disabled).toBe(false);
});

it('offers a return to the selected online voice when the device has no Vietnamese voice', async () => {
  (getAvailableVoicesAsync as jest.Mock).mockResolvedValue([]);
  const onReturn=jest.fn();
  await act(async()=>{ view=TestRenderer.create(<DeviceNarration paragraphs={['Em đọc lại đề nhé.']} onReturn={onReturn} />); });
  act(()=>view.root.findAll(node=>node.props.accessibilityLabel==='Quay lại giọng đã chọn'&&node.props.onPress)[0].props.onPress());
  expect(onReturn).toHaveBeenCalledTimes(1);expect(speak).not.toHaveBeenCalled();
});

it('keeps the same timeline UI and seeks to any whole word without speaking while paused', async () => {
  const parts = ['Em nhìn lại đề bài rồi tìm dữ kiện.', 'Sau đó em tìm số phần còn lại.'];
  const timeline = deviceTimeline(parts), ready = jest.fn(), position = jest.fn();
  await act(async () => { view=TestRenderer.create(<DeviceNarration paragraphs={parts} onReady={ready} onPosition={position}/>); });
  expect(ready).toHaveBeenCalledWith(timeline.cues);
  expect(player().props.estimatedTime).toBe(true);
  expect(JSON.stringify(view.toJSON())).toContain('Thời gian ước tính');
  const target=timeline.chunks[1].start+.8, located=devicePosition(timeline,target);
  act(()=>player().props.onSeek(target / timeline.duration * player().props.duration));
  expect(speak).not.toHaveBeenCalled(); expect(position).toHaveBeenLastCalledWith(located.time,timeline.duration);
  await act(async()=>player().props.onToggle());
  expect((speak as jest.Mock).mock.calls[0][0]).toBe(timeline.chunks[1].text.slice(located.offset));
});

it('tracks native word boundaries, pauses and resumes from the spoken word instead of the beginning', async () => {
  jest.useFakeTimers(); await render();
  await act(async()=>player().props.onToggle());
  const [text,events]=(speak as jest.Mock).mock.calls[0];
  const offset=text.indexOf('với');
  act(()=>{events.onStart(); events.onBoundary({charIndex:offset}); jest.advanceTimersByTime(500);});
  const shown=player().props.currentTime;
  act(()=>player().props.onToggle());
  expect(player().props.playing).toBe(false);
  expect(player().props.currentTime).toBe(shown);
  await act(async()=>player().props.onToggle());
  expect((speak as jest.Mock).mock.calls[1][0]).toBe(text.slice(offset));
  act(()=>{events.onDone();events.onError();events.onBoundary({charIndex:0});});
  expect(player().props.playing).toBe(true);
  expect(player().props.currentTime).toBeGreaterThanOrEqual(shown);
});

it('resumes a playing drag, retains a paused drag, changes speed and restarts only on request', async () => {
  await render(); await act(async()=>player().props.onToggle());
  const text=(speak as jest.Mock).mock.calls[0][0];
  act(()=>player().props.onScrubStart());
  expect(player().props.playing).toBe(false);
  await act(async()=>player().props.onSeek(text.indexOf('với') / text.length * player().props.duration));
  expect((speak as jest.Mock).mock.calls[1][0]).toBe('với 2 phần 5.');
  await act(async()=>player().props.onRate(1.2));
  expect((speak as jest.Mock).mock.lastCall[1].rate).toBeCloseTo(1.08);
  act(()=>player().props.onToggle());
  act(()=>player().props.onScrubStart()); act(()=>player().props.onSeek(0));
  expect(speak).toHaveBeenCalledTimes(3);
  await act(async()=>player().props.onRestart());
  expect((speak as jest.Mock).mock.lastCall[0]).toBe(text);
});

it('does not complete a reading from the estimated clock or from seeking to its end', async () => {
  jest.useFakeTimers(); const done=jest.fn(); await render(done);
  await act(async()=>player().props.onToggle());
  const events=(speak as jest.Mock).mock.calls[0][1]; act(()=>events.onStart());
  act(()=>jest.advanceTimersByTime(10000));
  expect(player().props.currentTime).toBeLessThan(player().props.duration);
  expect(done).not.toHaveBeenCalled();
  act(()=>player().props.onSeek(player().props.duration));
  act(()=>events.onDone()); expect(done).not.toHaveBeenCalled();
  await act(async()=>player().props.onRestart());
  act(()=>(speak as jest.Mock).mock.lastCall[1].onDone()); expect(done).toHaveBeenCalledTimes(1);
});

it('stops on app background and blur without autoplay on return or late slider events', async () => {
  let change!:(value:string)=>void;
  jest.spyOn(AppState,'addEventListener').mockImplementation((_,callback:any)=>{change=callback;return{remove:jest.fn()};});
  await render(); await act(async()=>player().props.onToggle());
  act(()=>change('background')); await act(async()=>player().props.onRestart());
  expect(speak).toHaveBeenCalledTimes(1);
  act(()=>change('active')); expect(speak).toHaveBeenCalledTimes(1);
  const blur=(mockNavigation.addListener as jest.Mock).mock.calls.find(call=>call[0]==='blur')![1];
  act(()=>blur()); await act(async()=>player().props.onRestart()); expect(speak).toHaveBeenCalledTimes(1);
});

it('cancels a native audio-session opening before it can speak after closing', async () => {
  let finish!:()=>void;
  (preparePlaybackSession as jest.Mock).mockImplementationOnce(()=>new Promise<void>(resolve=>{finish=resolve;}));
  await render(); await act(async()=>player().props.onToggle());
  act(()=>view.unmount()); await act(async()=>finish()); expect(speak).not.toHaveBeenCalled();
});

it('resets on new text and ignores late word events and voice inventories', async () => {
  await render(); await act(async()=>player().props.onToggle());
  const old=(speak as jest.Mock).mock.calls[0][1];
  await act(async()=>view.update(<DeviceNarration paragraphs={['Một bài hoàn toàn khác.']}/>));
  act(()=>{old.onDone();old.onBoundary({charIndex:10});});
  expect(player().props.currentTime).toBe(0);expect(player().props.playing).toBe(false);
  jest.useFakeTimers(); let finish!:(voices:any[])=>void;
  (getAvailableVoicesAsync as jest.Mock).mockImplementationOnce(()=>new Promise(resolve=>{finish=resolve;}));
  await act(async()=>view.update(<DeviceNarration paragraphs={['Bài mới nữa.']}/>));
  act(()=>jest.advanceTimersByTime(5000));
  await act(async()=>finish([{identifier:'late',language:'vi-VN'}]));
  expect(view.root.findAllByType(MediaTimeline)).toHaveLength(0);
});

it('bounds empty/nonfinite seeks and never splits a spoken word or changes math pronunciation', () => {
  expect(devicePosition(deviceTimeline([]), 8)).toEqual({index:0,offset:0,time:0});
  const timeline=deviceTimeline(['  ', 'Em cộng 1/3 với 2/5.']);
  expect(timeline.chunks[0].text).toContain('1 phần 3');
  expect(devicePosition(timeline,NaN).offset).toBe(0);
  expect(devicePosition(timeline,-10).time).toBe(0);
  expect(devicePosition(timeline,10000).time).toBe(timeline.duration);
  const position=devicePosition(timeline,.1);
  expect(timeline.chunks[position.index].text.slice(position.offset)).toMatch(/^Em /);
});

it('ignores stale events from a finished utterance and completes only once', async () => {
  const done=jest.fn();
  await act(async()=>{view=TestRenderer.create(<DeviceNarration paragraphs={['Một đoạn.', 'Một đoạn nữa.']} onFinished={done}/>);});
  await act(async()=>player().props.onToggle());
  const old=(speak as jest.Mock).mock.calls[0][1];
  act(()=>old.onDone());
  const position=player().props.currentTime;
  act(()=>{old.onDone();old.onBoundary({charIndex:0});old.onError();});
  expect(speak).toHaveBeenCalledTimes(2);expect(player().props.currentTime).toBe(position);
  const final=(speak as jest.Mock).mock.calls[1][1];
  act(()=>{final.onDone();final.onDone();});expect(done).toHaveBeenCalledTimes(1);
});

it('moves smoothly forward when delayed word positions arrive and keeps the thumb still on pause', async () => {
  jest.useFakeTimers(); await render(); await act(async()=>player().props.onToggle());
  const events=(speak as jest.Mock).mock.lastCall[1]; act(()=>events.onStart());
  const positions:number[]=[];
  for(let i=0;i<12;i++) {
    act(()=>jest.advanceTimersByTime(50)); positions.push(player().props.currentTime);
  }
  expect(new Set(positions).size).toBeGreaterThan(8);
  const before=player().props.currentTime;
  act(()=>events.onBoundary({charIndex:0})); expect(player().props.currentTime).toBeGreaterThanOrEqual(before);
  act(()=>jest.advanceTimersByTime(350)); const advanced=player().props.currentTime;
  expect(advanced).toBeGreaterThan(before);
  act(()=>events.onBoundary({charIndex:1})); expect(player().props.currentTime).toBeGreaterThanOrEqual(advanced);
  act(()=>player().props.onToggle()); expect(player().props.currentTime).toBeGreaterThanOrEqual(advanced);
  await act(async()=>player().props.onToggle()); expect(player().props.currentTime).toBeGreaterThanOrEqual(advanced);
  act(()=>player().props.onSeek(0)); expect(player().props.currentTime).toBe(0);
});

it('keeps delayed and irregular word corrections monotonic, bounded and gradual', () => {
  const progress=deviceProgress(0,20,1,0);
  let previous=0;
  for(let time=50;time<=25000;time+=50) {
    if(time%700===0) progress.boundary(Math.max(0,time/1800-1),time);
    const shown=progress.advance(time);
    expect(shown).toBeGreaterThanOrEqual(previous);
    expect(shown-previous).toBeLessThanOrEqual(.31);
    expect(shown).toBeLessThan(20);
    previous=shown;
  }
});

it('resumes near the current position when an engine never emits word boundaries', async () => {
  jest.useFakeTimers(); await render();await act(async()=>player().props.onToggle());
  const events=(speak as jest.Mock).mock.lastCall[1];act(()=>events.onStart());
  act(()=>jest.advanceTimersByTime(1000));const shown=player().props.currentTime;
  act(()=>player().props.onToggle());await act(async()=>player().props.onToggle());
  expect(player().props.currentTime).toBe(shown);
  const timeline=deviceTimeline(['Em cộng 1/3 với 2/5.']),target=devicePosition(timeline,shown/player().props.duration*timeline.duration);
  expect((speak as jest.Mock).mock.lastCall[0]).toBe(timeline.chunks[target.index].text.slice(target.offset));
  expect(target.offset).toBeGreaterThan(0);
});

it('keeps a real elapsed clock moving beyond the initial estimate and measures completion', async () => {
  jest.useFakeTimers(); await render(); await act(async()=>player().props.onToggle());
  const events=(speak as jest.Mock).mock.lastCall[1]; act(()=>events.onStart());
  const initial=player().props.duration;
  let previousTime=0, previousFraction=0;
  // No word events: even a slower engine must not freeze the time at its initial estimate.
  for(let tick=1;tick<=240;tick++) {
    act(()=>jest.advanceTimersByTime(50));
    const {currentTime,duration}=player().props;
    expect(currentTime-previousTime).toBeGreaterThan(.02);
    expect(currentTime-previousTime).toBeLessThan(.08);
    expect(currentTime/duration).toBeGreaterThan(previousFraction);
    previousTime=currentTime; previousFraction=currentTime/duration;
  }
  expect(previousTime).toBeGreaterThan(initial);
  act(()=>events.onDone());
  expect(player().props.currentTime).toBe(12); expect(player().props.duration).toBe(12);
});

it('runs one clock across utterances and groups adjacent short sentences', async () => {
  jest.useFakeTimers();
  await act(async()=>{view=TestRenderer.create(<DeviceNarration paragraphs={['Một câu. Câu kế tiếp.', 'Đoạn tiếp theo.']}/>);});
  await act(async()=>player().props.onToggle());
  expect((speak as jest.Mock).mock.lastCall[0]).toBe('Một câu. Câu kế tiếp.');
  const first=(speak as jest.Mock).mock.lastCall[1];
  act(()=>{first.onStart();jest.advanceTimersByTime(4000);first.onDone();});
  const second=(speak as jest.Mock).mock.lastCall[1];
  act(()=>{second.onStart();jest.advanceTimersByTime(3000);second.onDone();});
  expect(player().props.currentTime).toBe(7); expect(player().props.duration).toBe(7);
});

it('calibrates the entire estimate from sparse words without backward or stationary frames', () => {
  const clock=deviceProgress(0,9,1,0); let previous=0;
  for(let time=50;time<12000;time+=50) {
    if(time%1000===0) clock.boundary(time/1000*.75,time);
    const fraction=clock.advance(time)/9;
    expect(fraction).toBeGreaterThan(previous);
    expect(fraction-previous).toBeLessThan(.02);
    previous=fraction;
  }
  expect(clock.duration).toBeGreaterThan(11.95); expect(clock.duration).toBeLessThan(13);
  expect(clock.finish(12000)).toBe(12);
});

it('resumes inside a later utterance when the engine supplies no word boundaries', async () => {
  jest.useFakeTimers();
  const parts=['Đọc đề.', 'Sau đó em nhìn dấu phép cộng và tự đếm thêm từng phần bằng nhau để tìm kết quả của câu hỏi.'];
  const report=jest.fn(),done=jest.fn();
  await act(async()=>{view=TestRenderer.create(<DeviceNarration paragraphs={parts} onPosition={report} onFinished={done}/>);});
  await act(async()=>player().props.onToggle());const first=(speak as jest.Mock).mock.lastCall[1];
  act(()=>{first.onStart();jest.advanceTimersByTime(1000);first.onDone();});
  const second=(speak as jest.Mock).mock.lastCall[1];
  act(()=>{second.onStart();jest.advanceTimersByTime(2000);player().props.onToggle();});
  const [seconds]=report.mock.lastCall;
  const timeline=deviceTimeline(parts),target=devicePosition(timeline,seconds);
  expect(target.index).toBe(1);expect(target.offset).toBeGreaterThan(0);
  await act(async()=>player().props.onToggle());
  expect((speak as jest.Mock).mock.lastCall[0]).toBe(timeline.chunks[1].text.slice(target.offset));
  act(()=>{first.onDone();second.onDone();second.onError();});
  expect(done).not.toHaveBeenCalled();expect(player().props.playing).toBe(true);
});

it('learns bounded per-voice pace only from plausible complete readings', () => {
  expect(estimatedDeviceDuration('pace-new',120)).toBe(10);
  rememberDevicePace('pace-new',120,12);
  expect(estimatedDeviceDuration('pace-new',120)).toBe(12);
  expect(estimatedDeviceDuration('pace-other',120)).toBe(10);
  rememberDevicePace('pace-new',10,12);rememberDevicePace('pace-new',120,Infinity);
  expect(estimatedDeviceDuration('pace-new',120)).toBe(12);
  for(let voice=0;voice<9;voice++)rememberDevicePace(`pace-bounded-${voice}`,120,15);
  expect(estimatedDeviceDuration('pace-new',120)).toBe(10);
});

it('does not move the clock backwards when the system wall clock changes', async () => {
  jest.useFakeTimers();await render();await act(async()=>player().props.onToggle());
  const events=(speak as jest.Mock).mock.lastCall[1];act(()=>{events.onStart();jest.advanceTimersByTime(1500);});
  const shown=player().props.currentTime;
  act(()=>{jest.setSystemTime(Date.now()-60000);jest.advanceTimersByTime(100);});
  expect(player().props.currentTime).toBeGreaterThan(shown);
  act(()=>{jest.setSystemTime(Date.now()+3600000);jest.advanceTimersByTime(100);});
  expect(player().props.currentTime).toBeLessThan(shown+.25);
});
