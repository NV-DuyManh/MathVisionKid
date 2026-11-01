import { AppState, Platform, type AppStateStatus } from 'react-native';
import { createAudioPlayer, setAudioModeAsync } from 'expo-audio';
import { File } from 'expo-file-system';
import { NativeAudioController } from '../features/training-games/nativeAudioController';
import { NativeAudioController as BrowserAudioController } from '../features/training-games/nativeAudioController.web';
import { AudioController } from '@mathvisionkid/training-games';

jest.mock('expo-audio', () => ({ createAudioPlayer: jest.fn(), setAudioModeAsync: jest.fn() }));
jest.mock('expo-file-system', () => ({
  Paths: { cache: 'file:///private/cache/' },
  File: jest.fn().mockImplementation((_directory: string, name: string) => ({
    uri: 'file:///private/cache/' + name, create: jest.fn(), writeSync: jest.fn(), delete: jest.fn(),
  })),
}));

type Player = { play: jest.Mock; pause: jest.Mock; remove: jest.Mock; unsubscribe: jest.Mock; finish: () => void; addListener: jest.Mock };
const players: Player[] = [], controllers: NativeAudioController[] = [];
let onAppState: ((state: AppStateStatus) => void) | undefined;
let removeAppState: jest.Mock;
const makeController = (onChange?: (enabled: boolean) => void) => {
  const controller = new NativeAudioController(onChange); controllers.push(controller); return controller;
};
const settle = async () => { await Promise.resolve(); await Promise.resolve(); await Promise.resolve(); };
const files = () => jest.mocked(File).mock.results.map(result => result.value as { uri: string; create: jest.Mock; writeSync: jest.Mock; delete: jest.Mock });

beforeEach(() => {
  jest.useFakeTimers(); jest.clearAllMocks(); players.length = 0;
  removeAppState = jest.fn();
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_event, listener) => { onAppState = listener; return { remove: removeAppState }; });
  jest.mocked(setAudioModeAsync).mockResolvedValue(undefined);
  jest.mocked(createAudioPlayer).mockImplementation(() => {
    let onStatus: ((status: { didJustFinish: boolean }) => void) | undefined;
    const player: Player = { play: jest.fn(), pause: jest.fn(), remove: jest.fn(), unsubscribe: jest.fn(),
      finish: () => onStatus?.({ didJustFinish: true }),
      addListener: jest.fn((_event, listener) => { onStatus = listener; return { remove: player.unsubscribe }; }),
    };
    players.push(player); return player as unknown as ReturnType<typeof createAudioPlayer>;
  });
});
afterEach(() => {
  controllers.splice(0).forEach(controller => controller.dispose());
  jest.restoreAllMocks(); jest.useRealTimers();
});

test.each(['android', 'ios'] as const)('%s plays a valid non-silent local WAV after resetting recording audio mode', async os => {
  jest.replaceProperty(Platform, 'OS', os);
  const controller = makeController(); controller.playTap(); await settle();
  expect(setAudioModeAsync).toHaveBeenCalledWith({ allowsRecording: false, playsInSilentMode: true, shouldPlayInBackground: false,
    shouldRouteThroughEarpiece: false, interruptionMode: 'mixWithOthers' });
  expect(jest.mocked(setAudioModeAsync).mock.invocationCallOrder[0]).toBeLessThan(jest.mocked(createAudioPlayer).mock.invocationCallOrder[0]);
  expect(createAudioPlayer).toHaveBeenCalledWith({ uri: files()[0].uri }, { keepAudioSessionActive: false, updateInterval: 50 });
  expect(players[0].play).toHaveBeenCalledTimes(1);
  const bytes = files()[0].writeSync.mock.calls[0][0] as Uint8Array, view = new DataView(bytes.buffer);
  expect(String.fromCharCode(...bytes.slice(0, 4))).toBe('RIFF'); expect(String.fromCharCode(...bytes.slice(8, 12))).toBe('WAVE');
  expect(view.getUint16(20, true)).toBe(1); expect(view.getUint16(22, true)).toBe(1); expect(view.getUint16(34, true)).toBe(16);
  expect(view.getUint32(24, true)).toBe(22050); expect(view.getUint32(40, true)).toBe(bytes.length - 44);
  expect(bytes.slice(44).some(sample => sample !== 0)).toBe(true);
  players[0].finish(); expect(players[0].remove).toHaveBeenCalledTimes(1); expect(files()[0].delete).toHaveBeenCalledTimes(1);
});

test('native shares the package API, keeps web synthesis, and cancels a chime when sound is switched off', async () => {
  expect(BrowserAudioController).toBe(AudioController);
  const persist = jest.fn(), controller = makeController(persist);
  controller.playCorrect(); await settle(); expect(players).toHaveLength(1);
  controller.setSoundEnabled(false); expect(persist).toHaveBeenLastCalledWith(false);
  expect(players[0].pause).toHaveBeenCalled(); expect(players[0].remove).toHaveBeenCalled();
  controller.setSoundEnabled(true, false); jest.advanceTimersByTime(500); await settle();
  expect(players).toHaveLength(1); expect(persist).toHaveBeenCalledTimes(1);
  controller.playIncorrect(); controller.playCannonShoot(); controller.playRhythmBeat(); await settle();
  expect(players).toHaveLength(4);
  controller.playVictory(); jest.advanceTimersByTime(360); await settle(); expect(players).toHaveLength(8);
});

test('backgrounding stops and releases sounds, drops scheduled notes and resumes only on a fresh foreground action', async () => {
  const controller = makeController(); controller.playCorrect(); await settle();
  onAppState?.('background'); expect(players[0].remove).toHaveBeenCalled();
  controller.playTap(); jest.advanceTimersByTime(500); await settle(); expect(players).toHaveLength(1);
  onAppState?.('active'); controller.playTap(); await settle(); expect(players).toHaveLength(2);
  controller.dispose(); expect(removeAppState).toHaveBeenCalledTimes(1); expect(jest.getTimerCount()).toBe(0);
});

test('late audio-mode completion from a disposed student cannot create or play audio for the next student', async () => {
  let completeOld!: () => void;
  jest.mocked(setAudioModeAsync).mockImplementationOnce(() => new Promise(resolve => { completeOld = resolve; }));
  const old = makeController(); old.playCorrect(); old.dispose();
  const next = makeController(); next.playTap(); await settle(); expect(players).toHaveLength(1);
  completeOld(); jest.advanceTimersByTime(500); await settle();
  expect(players).toHaveLength(1); expect(players[0].play).toHaveBeenCalledTimes(1); expect(players[0].remove).not.toHaveBeenCalled();
  old.playTap(); old.setSoundEnabled(true); await settle(); expect(players).toHaveLength(1);
});

test('rapid taps keep at most four native players, and a failed completion is bounded by a release watchdog', async () => {
  const controller = makeController(); for (let index = 0; index < 12; index++) controller.playTap();
  await settle(); expect(players).toHaveLength(12); expect(players.filter(player => !player.remove.mock.calls.length)).toHaveLength(4);
  jest.advanceTimersByTime(2000); expect(players.every(player => player.remove.mock.calls.length === 1)).toBe(true);
  expect(files().every(file => file.delete.mock.calls.length === 1)).toBe(true); expect(jest.getTimerCount()).toBe(0);
});

test('audio errors leave gameplay usable and dispose all partially created resources', async () => {
  const controller = makeController(); jest.mocked(setAudioModeAsync).mockRejectedValueOnce(Error('interrupted'));
  controller.playTap(); await settle(); expect(createAudioPlayer).not.toHaveBeenCalled();
  jest.mocked(createAudioPlayer).mockImplementationOnce(() => { throw Error('unavailable'); });
  controller.playTap(); await settle(); expect(files()[0].delete).toHaveBeenCalledTimes(1);
  controller.playTap(); await settle(); expect(players[0].play).toHaveBeenCalledTimes(1);
  controller.dispose(); expect(players[0].remove).toHaveBeenCalledTimes(1); expect(jest.getTimerCount()).toBe(0);
});
