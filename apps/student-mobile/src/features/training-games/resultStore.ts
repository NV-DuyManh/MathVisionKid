import AsyncStorage from '@react-native-async-storage/async-storage';
import { isStudentUuid, isTrainingGameId, type TrainingEvent, type TrainingGameId, type TrainingSessionResult } from '@mathvisionkid/training-games';

type Storage = Pick<typeof AsyncStorage, 'getItem' | 'setItem'>;
type Envelope = { schemaVersion: 1; results: TrainingSessionResult[]; events: TrainingEvent[] };
type Write = { kind: 'result'; value: TrainingSessionResult } | { kind: 'event'; value: TrainingEvent };
export class TrainingResultStore {
  private queues = new Map<string, Promise<void>>();
  private pending = new Map<string, Map<string, Write>>();
  private errors = new Map<string, string>();
  private listeners = new Set<() => void>();
  constructor(private readonly storage: Storage = AsyncStorage) {}
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private notify() { this.listeners.forEach(listener => listener()); }
  private key(studentId: string, gameId: TrainingGameId) {
    if (!isStudentUuid(studentId) || !isTrainingGameId(gameId)) throw new Error('Invalid training identity');
    return `@mathvisionkid:training:v1:${studentId.toLowerCase()}:${gameId}:host-results`;
  }
  error(studentId: string) { return [...this.errors].some(([key]) => key.startsWith(`@mathvisionkid:training:v1:${studentId}:`)) ? 'Chưa lưu được kết quả trên thiết bị. Em có thể thử lưu lại.' : null; }
  private async read(key: string): Promise<Envelope> {
    const raw = await this.storage.getItem(key);
    if (!raw) return { schemaVersion: 1, results: [], events: [] };
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== 'object' || !('schemaVersion' in value) || value.schemaVersion !== 1 || !('results' in value) || !Array.isArray(value.results) || !('events' in value) || !Array.isArray(value.events)) throw new Error('Invalid local training data');
    return value as Envelope;
  }
  private enqueue(studentId: string, gameId: TrainingGameId, write: Write) {
    const key = this.key(studentId, gameId);
    if (write.value.studentId !== studentId || write.value.gameId !== gameId || write.value.schemaVersion !== 1) return Promise.reject(new Error('Training owner mismatch'));
    const pending = this.pending.get(key) ?? new Map<string, Write>();
    const captured: Write = write.kind === 'result' ? { kind: 'result', value: { ...write.value, skillsPracticed: [...write.value.skillsPracticed] } } : { kind: 'event', value: { ...write.value } };
    pending.set(write.value.eventId, captured); this.pending.set(key, pending);
    return this.flushKey(key);
  }
  save(studentId: string, result: TrainingSessionResult): Promise<void> {
    if (result.eventId !== `${result.sessionId}:result:v1` || result.syncStatus !== 'local-only' || !['won','lost','abandoned','restarted'].includes(result.status)) return Promise.reject(new Error('Invalid training result'));
    const metrics = [result.playtimeSeconds, result.score, result.maxScore, result.correctCount, result.incorrectCount];
    if (metrics.some(value => value !== undefined && (!Number.isFinite(value) || value < 0))) return Promise.reject(new Error('Invalid training metrics'));
    return this.enqueue(studentId, result.gameId, { kind: 'result', value: result });
  }
  event(studentId: string, event: TrainingEvent) { return this.enqueue(studentId, event.gameId, { kind: 'event', value: event }); }
  private flushKey(key: string): Promise<void> {
    const task = (this.queues.get(key) ?? Promise.resolve()).catch(() => {}).then(async () => {
      const pending = this.pending.get(key);
      if (!pending?.size) return;
      const batch = [...pending.entries()];
      const envelope = await this.read(key);
      for (const [, write] of batch) {
        if (write.kind === 'result') { if (!envelope.results.some(row => row.sessionId === write.value.sessionId)) envelope.results.unshift(write.value); }
        else if (!envelope.events.some(row => row.eventId === write.value.eventId)) envelope.events.push(write.value);
      }
      envelope.results = envelope.results.slice(0, 100); envelope.events = envelope.events.slice(-300);
      await this.storage.setItem(key, JSON.stringify(envelope));
      for (const [id, value] of batch) if (pending.get(id) === value) pending.delete(id);
      this.errors.delete(key); this.notify();
    }).catch(error => { this.errors.set(key, 'storage'); this.notify(); throw error; });
    this.queues.set(key, task); return task;
  }
  async retry(studentId: string) {
    await Promise.all([...this.pending.keys()].filter(key => key.startsWith(`@mathvisionkid:training:v1:${studentId}:`)).map(key => this.flushKey(key)));
  }
  async history(studentId: string, gameId: TrainingGameId) { return (await this.read(this.key(studentId, gameId))).results; }
}
export const trainingResults = new TrainingResultStore();
