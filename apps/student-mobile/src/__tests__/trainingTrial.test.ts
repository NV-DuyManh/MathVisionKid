import AsyncStorage from '@react-native-async-storage/async-storage';
import { isStudentUuid } from '@mathvisionkid/training-games';
import { trainingAccess, trainingStudentId } from '../features/training-games/identity';
import { createTrainingRuntime } from '../features/training-games/runtime';
import { trainingResults } from '../features/training-games/resultStore';

// Native audio I/O is covered separately in trainingNativeAudio.test.ts.
jest.mock('../features/training-games/nativeAudioController', () => ({ NativeAudioController: require('@mathvisionkid/training-games').AudioController }));

const A = '66666666-6666-4666-8666-666666666666';
const mockA = { userId: 'mock_student_a', role: 'STUDENT' };
const mockB = { userId: 'mock_student_b', role: 'STUDENT' };
afterEach(() => jest.restoreAllMocks());

test('native /me userId and web normalized id both keep the real UUID, including when a trial URL is requested', () => {
  expect(trainingStudentId({ userId: A, role: 'STUDENT' }, true)).toBe(A);
  expect(trainingStudentId({ id: A, role: 'ROLE_STUDENT' }, true)).toBe(A);
  expect(trainingAccess({ userId: A, role: 'STUDENT' }, true, true)).toEqual({ kind: 'student', studentId: A });
  expect(trainingAccess({ userId: A, role: 'STUDENT' }, true, false)).toEqual({ kind: 'student', studentId: A });
});

test('trial is limited to authenticated, active mock students in development; no production or arbitrary-role bypass', () => {
  expect(trainingAccess(mockA, true, true).kind).toBe('trial');
  expect(trainingAccess(mockA, true, false).kind).toBe('blocked');
  expect(trainingAccess(mockA, false, true).kind).toBe('blocked');
  expect(trainingAccess({ ...mockA, active: false }, true, true).kind).toBe('blocked');
  expect(trainingAccess({ ...mockA, role: 'TEACHER' }, true, true).kind).toBe('blocked');
  expect(trainingAccess({ userId: 'malformed-real-id', role: 'STUDENT' }, true, true).kind).toBe('blocked');
  expect(trainingAccess({ userId: A, active: false, role: 'STUDENT' }, true, true).kind).toBe('blocked');
});

test('trial owners are opaque non-UUIDs, stable per auth object, and different for A and B', () => {
  const a = trainingAccess(mockA, true, true), b = trainingAccess(mockB, true, true);
  expect(a.kind).toBe('trial'); expect(b.kind).toBe('trial');
  if (a.kind !== 'trial' || b.kind !== 'trial') throw Error('Expected trial access');
  expect(a.owner).not.toBe(b.owner); expect(isStudentUuid(a.owner)).toBe(false);
  expect(a.owner).not.toContain(mockA.userId); expect(trainingAccess(mockA, true, true)).toEqual(a);
});

test('trial gameplay writes and terminal callbacks never reach real student storage, achievements or the network', async () => {
  const save = jest.spyOn(trainingResults, 'save'), event = jest.spyOn(trainingResults, 'event');
  const writes = jest.spyOn(AsyncStorage, 'setItem'), network = jest.spyOn(global, 'fetch');
  const a = createTrainingRuntime('development-trial:9001', 'planet-rescue', true);
  const b = createTrainingRuntime('development-trial:9002', 'planet-rescue', true);
  await Promise.all([a.ready, b.ready]);
  await a.services.storage.setItem('construction', 'A');
  expect(await b.services.storage.getItem('construction')).toBeNull();
  await b.services.storage.setItem('construction', 'B');
  expect(await a.services.storage.getItem('construction')).toBe('A');
  a.services.bridge.observe({ attemptId: 'trial-attempt', started: true, paused: false, mode: 'easy', status: 'won', skillsPracticed: [] });
  const lateStorage = a.services.storage, lateBridge = a.services.bridge;
  a.dispose();
  await lateStorage.setItem('construction', 'obsolete-A');
  lateBridge.observe({ attemptId: 'obsolete', started: true, paused: false, mode: 'easy', status: 'won', skillsPracticed: [] });
  expect(await lateStorage.getItem('construction')).toBeNull();
  expect(await b.services.storage.getItem('construction')).toBe('B');
  const reopened = createTrainingRuntime('development-trial:9001', 'planet-rescue', true);
  await reopened.ready; expect(await reopened.services.storage.getItem('construction')).toBeNull();
  expect(writes).not.toHaveBeenCalled(); expect(save).not.toHaveBeenCalled(); expect(event).not.toHaveBeenCalled(); expect(network).not.toHaveBeenCalled();
  b.dispose(); reopened.dispose();
});

test('runtime rejects a real UUID masquerading as a trial and does not accept trial IDs for student persistence', () => {
  expect(() => createTrainingRuntime(A, 'planet-rescue', true)).toThrow('cannot use a student UUID');
  expect(() => createTrainingRuntime('development-trial:9001', 'planet-rescue')).toThrow();
});
