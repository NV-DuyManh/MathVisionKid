jest.mock('../features/tutoring/voicePreferences', () => ({ voicePreferences: { get: jest.fn(), set: jest.fn() } }));

function fresh() {
  jest.resetModules();
  const { voicePreferences } = require('../features/tutoring/voicePreferences');
  const voices = require('../features/tutoring/narrationVoices');
  voicePreferences.get.mockResolvedValue(null);
  voicePreferences.set.mockResolvedValue(undefined);
  return { voicePreferences, ...voices };
}

it('retains the chosen voice through later sheets without reading stale storage again', async () => {
  const { voicePreferences, saveNarrationVoice, readNarrationVoice, currentNarrationVoice } = fresh();
  voicePreferences.get.mockResolvedValue(JSON.stringify({ voiceId: 'vi-VN-NamMinhNeural' }));
  await readNarrationVoice();
  await saveNarrationVoice('vi-VN-HoaiMyNeural');
  await expect(readNarrationVoice()).resolves.toBe('vi-VN-HoaiMyNeural');
  expect(currentNarrationVoice()).toBe('vi-VN-HoaiMyNeural');
  expect(voicePreferences.get).toHaveBeenCalledTimes(1);
});

it('uses the latest chosen voice immediately while storage is still saving', async () => {
  const { voicePreferences, saveNarrationVoice, readNarrationVoice } = fresh();
  let finish!: () => void;
  voicePreferences.set.mockImplementationOnce(() => new Promise<void>(resolve => { finish = resolve; }));
  const saving = saveNarrationVoice('vi-VN-HoaiMyNeural');
  await expect(readNarrationVoice()).resolves.toBe('vi-VN-HoaiMyNeural');
  expect(voicePreferences.get).not.toHaveBeenCalled();
  finish(); await saving;
});

it('serializes rapid preference writes so an older write cannot overwrite the latest voice', async () => {
  const { voicePreferences, saveNarrationVoice, readNarrationVoice } = fresh();
  let finish!: () => void;
  voicePreferences.set.mockImplementationOnce(() => new Promise<void>(resolve => { finish = resolve; }));
  const first = saveNarrationVoice('vi-VN-NamMinhNeural');
  await Promise.resolve();
  const last = saveNarrationVoice('vi-VN-HoaiMyNeural');
  await expect(readNarrationVoice()).resolves.toBe('vi-VN-HoaiMyNeural');
  expect(voicePreferences.set).toHaveBeenCalledTimes(1);
  finish(); await first; await last;
  expect(voicePreferences.set).toHaveBeenLastCalledWith(JSON.stringify({ voiceId: 'vi-VN-HoaiMyNeural' }));
});

it('keeps the current choice after a storage failure and allows a later save to recover', async () => {
  const { voicePreferences, saveNarrationVoice, readNarrationVoice, subscribeNarrationVoice } = fresh();
  const changed = jest.fn(), remove = subscribeNarrationVoice(changed);
  voicePreferences.set.mockRejectedValueOnce(new Error('storage unavailable'));
  await expect(saveNarrationVoice('vi-VN-HoaiMyNeural')).rejects.toThrow('storage unavailable');
  await expect(readNarrationVoice()).resolves.toBe('vi-VN-HoaiMyNeural');
  remove();
  await saveNarrationVoice('vi-VN-NamMinhNeural');
  expect(changed).toHaveBeenCalledTimes(1);
  expect(voicePreferences.set).toHaveBeenLastCalledWith(JSON.stringify({ voiceId: 'vi-VN-NamMinhNeural' }));
});
