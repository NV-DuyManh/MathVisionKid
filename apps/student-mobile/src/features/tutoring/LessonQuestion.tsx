import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, AppState, Keyboard, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { File } from 'expo-file-system';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { LessonReply, TutorService } from './api/TutorService';
import { LessonNarration } from './LessonNarration';
import { useQuestionRecorder } from './useQuestionRecorder';
import { QuestionRecording } from './QuestionRecording';
import { TaskProgress } from '../../components/ui/TaskProgress';

type Props = { sessionId: string; revision: number; stepIndex: number; scope: string };
export function LessonQuestion(props: Props) {
  return <QuestionSession key={JSON.stringify([props.scope, props.sessionId, props.revision, props.stepIndex])} {...props} />;
}
function QuestionSession({ sessionId, revision, stepIndex, scope }: Props) {
  const { recorder, durationMillis } = useQuestionRecorder();
  const [question, setQuestion] = useState(''), [reply, setReply] = useState<LessonReply | null>(null);
  const [phase, setPhase] = useState<'idle' | 'preparing' | 'recording' | 'transcribing' | 'asking' | 'stopping'>('idle');
  const [notice, setNotice] = useState('');
  const [transcribingStep, setTranscribingStep] = useState(0);
  const [recording, setRecording] = useState<{ uri: string; durationMillis: number } | null>(null);
  const recordingUri = useRef<string | null>(null);
  const recordedDuration = useRef(durationMillis);
  useEffect(() => { recordedDuration.current = durationMillis; }, [durationMillis]);
  const active = useRef(true), ownedRecording = useRef(false), timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pending = useRef<AbortController | null>(null), generation = useRef(0), busy = useRef(false);
  const stopping = useRef(false);
  const clean = (uri: string | null) => { if (!uri) return; try {
    if (Platform.OS === 'web') { if (uri.startsWith('blob:')) URL.revokeObjectURL(uri); }
    else if (uri.startsWith('file:')) new File(uri).delete();
  } catch { /* The recorder cache may already have been released. */ } };
  const endRecording = useCallback(async () => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    ownedRecording.current = false;
    return recorder.stop().catch(() => null);
  }, [recorder]);
  const cancel = useCallback(() => {
    if (stopping.current) return;
    stopping.current = true;
    const id = ++generation.current;
    pending.current?.abort(); busy.current = true;
    if (active.current) setPhase('stopping');
    void endRecording().then(uri => { if (uri !== recordingUri.current) clean(uri); }).finally(() => {
      stopping.current = false;
      if (active.current && id === generation.current) { busy.current = false; setPhase('idle'); setNotice('Đã dừng. Em có thể gõ câu hỏi.'); }
    });
  }, [endRecording]);
  useEffect(() => {
    active.current = true;
    const listener = AppState.addEventListener('change', state => { if (state !== 'active') cancel(); });
    return () => { active.current = false; listener.remove(); cancel(); clean(recordingUri.current); recordingUri.current = null; };
  }, [scope, cancel]);
  const finish = async () => {
    if (!ownedRecording.current) return;
    const id = generation.current;
    setTranscribingStep(0); setPhase('transcribing'); const uri = await endRecording();
    if (!active.current || id !== generation.current) { clean(uri); return; }
    const controller = new AbortController(); pending.current = controller;
    try {
      if (!uri) throw new Error('no recording');
      recordingUri.current = uri; setRecording({ uri, durationMillis: recordedDuration.current });
      setTranscribingStep(1);
      const text = await TutorService.transcribeQuestion(uri, controller.signal);
      if (active.current && id === generation.current) { setQuestion(text); setReply(null); setNotice('Em đọc lại, sửa nếu cần rồi bấm Gửi câu hỏi.'); }
    } catch {
      if (active.current && id === generation.current) setNotice('Chưa nghe rõ lúc này. Em thử ghi lại hoặc gõ câu hỏi nhé.');
    } finally {
      if (active.current && id === generation.current) { busy.current = false; setPhase('idle'); }
    }
  };
  const start = async () => {
    if (busy.current) return;
    busy.current = true; const id = ++generation.current; setNotice(''); setReply(null); setPhase('preparing');
    clean(recordingUri.current); recordingUri.current = null; setRecording(null);
    try {
      await recorder.prepare();
      if (!active.current || id !== generation.current) { clean(await recorder.stop()); return; }
      ownedRecording.current = true; recorder.start(() => { void finish(); });
      setPhase('recording'); setReply(null);
      timer.current = setTimeout(() => { void finish(); }, 31000);
    } catch {
      if (active.current && id === generation.current) {
        clean(await recorder.stop().catch(() => null));
        busy.current = false; setPhase('idle'); setNotice('Chưa dùng được mic. Em cho phép ghi âm hoặc gõ câu hỏi bên dưới nhé.');
      }
    }
  };
  const ask = async () => {
    if (busy.current || question.trim().length < 2) return;
    Keyboard.dismiss();
    busy.current = true; const id = ++generation.current, controller = new AbortController(); pending.current = controller;
    setPhase('asking'); setNotice(''); setReply(null);
    try {
      const answer = await TutorService.askLesson({ sessionId, revision, stepIndex, question: question.trim() }, controller.signal);
      if (active.current && id === generation.current) setReply(answer);
    } catch {
      if (active.current && id === generation.current) setNotice('Chưa trả lời được lúc này. Câu hỏi vẫn được giữ; em thử lại nhé.');
    } finally {
      if (active.current && id === generation.current) { busy.current = false; setPhase('idle'); }
    }
  };
  const waiting = phase !== 'idle' && phase !== 'recording';
  return <View style={[styles.stack, waiting && styles.waitingLayout]}>
    {reply ? <View style={styles.questionBubble}><Text style={styles.smallLabel}>CÂU HỎI CỦA EM</Text><MathText style={styles.body}>{question}</MathText></View>
      : !waiting ? <Text style={styles.intro}>Em muốn hỏi chỗ nào?</Text> : null}
    {phase === 'recording' ? <View style={styles.recording}>
      <View style={styles.recordingHeading}><View style={styles.micBadge}><Ionicons name="mic" size={24} color="#A84255" accessible={false} /></View><View style={styles.recordingTitle}><Text style={styles.intro}>Mình đang nghe em</Text><Text style={styles.caption}>Nói xong, em bấm nút bên dưới nhé.</Text></View></View>
      <View style={styles.recordingTime}><View style={styles.recordingDot} /><Text style={styles.timer}>{Math.min(30, Math.floor(durationMillis / 1000))} / 30 giây</Text></View>
      <View accessibilityRole="progressbar" accessibilityLabel="Thời gian ghi âm" accessibilityValue={{ min: 0, max: 30, now: Math.min(30, Math.floor(durationMillis / 1000)) }} style={styles.recordingTrack}><View style={[styles.recordingFill, { width: `${Math.min(100, Math.max(0, durationMillis / 300))}%` }]} /></View>
      <AppButton title="Nói xong" onPress={() => { void finish(); }} />
    </View> : phase === 'idle' ? !reply ? <>
      {recording ? <QuestionRecording key={recording.uri} uri={recording.uri} durationMillis={recording.durationMillis} /> : null}
      <Pressable accessibilityRole="button" accessibilityLabel="Ghi âm câu hỏi" style={({ pressed }) => [styles.mic, pressed && { opacity: .7 }]} onPress={() => { void start(); }}>
        <Ionicons name={recording ? 'refresh' : 'mic-outline'} size={25} color={COLORS.primaryDark} /><Text style={styles.label}>{recording ? 'Nói lại câu hỏi' : 'Nhấn để nói câu hỏi'}</Text></Pressable>
      {!recording ? <Text style={styles.caption}>Nói tối đa 30 giây, mình sẽ chuyển thành chữ để em kiểm tra. Em chỉ đọc nội dung bài học nhé.</Text> : null}
      <View style={styles.inputHeading}><Text style={styles.inputLabel}>{question ? 'Kiểm tra câu hỏi của em' : 'Hoặc gõ câu hỏi'}</Text>{question.length > 400 ? <Text style={styles.count}>{question.length}/500</Text> : null}</View>
      <TextInput accessibilityLabel="Câu hỏi của em" value={question} onChangeText={setQuestion} maxLength={500} multiline style={styles.input}
        placeholder="Ví dụ: Vì sao phải quy đồng?" placeholderTextColor={COLORS.textSecondary} />
      <AppButton title="Gửi câu hỏi" disabled={question.trim().length < 2} onPress={() => { void ask(); }} />
    </> : null : phase === 'asking' || phase === 'transcribing' ? <View style={styles.progressPanel}>
      <Text style={styles.intro}>{phase === 'asking' ? 'Mình cùng tìm hiểu nhé' : 'Mình đang nghe lại câu hỏi'}</Text>
      <TaskProgress steps={phase === 'asking' ? ['Câu hỏi đã nhập', 'Soạn lời giải thích', 'Mở câu trả lời'] : ['Lưu câu hỏi vừa nói', 'Chuyển lời nói thành chữ', 'Mở phần kiểm tra']}
        activeStep={phase === 'asking' ? 1 : transcribingStep} />
    </View> : <View style={styles.waiting} accessibilityLiveRegion="polite" aria-busy><ActivityIndicator color={COLORS.primaryDark} /><Text style={styles.waitingText}>{phase === 'stopping' ? 'Đang dừng mic…' : 'Đang mở mic…'}</Text></View>}
    {phase !== 'idle' && phase !== 'stopping' ? <AppButton title={phase === 'recording' ? 'Hủy ghi âm' : 'Dừng'} variant="ghost" onPress={cancel} /> : null}
    {notice ? <Text accessibilityLiveRegion="polite" style={styles.body}>{notice}</Text> : null}
    {reply ? <View style={styles.reply} accessibilityLiveRegion="polite">
      <View style={styles.answerHeading}><Ionicons name="sparkles-outline" size={19} color="#8C68D1" accessible={false}/><Text style={styles.answerTitle}>Mình cùng tìm hiểu</Text></View><MathText style={styles.body}>{reply.answer}</MathText>
      {reply.followUp ? <View style={styles.followUp}><Text style={styles.smallLabel}>EM THỬ NGHĨ NHÉ</Text><MathText style={styles.body}>{reply.followUp}</MathText></View> : null}
      <LessonNarration compact scope={`${scope}:reply:${reply.answer}`} source={{ sessionId, revision }} paragraphs={[reply.spokenExplanation, reply.followUp]} />
      <AppButton title="Hỏi thêm chỗ này" variant="ghost" onPress={() => { setReply(null); setQuestion(''); setNotice(''); }} />
    </View> : null}
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: 13 }, body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 15, lineHeight: 25 },
  intro: { fontFamily: FONTS.bold, color: COLORS.textPrimary, fontSize: 18, lineHeight: 27 },
  questionBubble: { borderRadius: 18, backgroundColor: '#F5F2FA', padding: 16, gap: 8 }, smallLabel: { fontFamily: FONTS.extraBold, fontSize: 10, lineHeight: 17, letterSpacing: .6, color: '#7E6A91' },
  answerHeading: { flexDirection: 'row', alignItems: 'center', gap: 7 }, answerTitle: { fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 24, color: '#3C2D56' },
  followUp: { borderLeftWidth: 3, borderLeftColor: '#D7C6F3', paddingLeft: 13, paddingVertical: 3, gap: 5 },
  caption: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 12, lineHeight: 19 },
  label: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 16, lineHeight: 24 },
  mic: { minHeight: 60, borderRadius: 18, padding: 16, backgroundColor: '#F1ECFF', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  input: { minHeight: 110, borderRadius: 16, borderWidth: 1.5, borderColor: '#D6CDEF', padding: 15, fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25, color: COLORS.textPrimary, textAlignVertical: 'top' },
  inputHeading: { flexDirection: 'row', alignItems: 'center', gap: 8 }, inputLabel: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, lineHeight: 23, color: COLORS.textPrimary }, count: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary, fontVariant: ['tabular-nums'] },
  recording: { borderRadius: 22, backgroundColor: '#FCFAFF', borderWidth: 1, borderColor: '#E8DFF3', padding: 18, gap: 16 },
  recordingHeading: { flexDirection: 'row', alignItems: 'center', gap: 12 }, recordingTitle: { flex: 1, gap: 3 }, micBadge: { width: 46, height: 46, borderRadius: 16, backgroundColor: '#FBE9ED', alignItems: 'center', justifyContent: 'center' },
  recordingTime: { flexDirection: 'row', alignItems: 'center', gap: 7 }, recordingDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#B64E62' }, timer: { fontFamily: FONTS.bold, fontSize: 13, color: '#8E3D50', fontVariant: ['tabular-nums'] },
  recordingTrack: { height: 5, backgroundColor: '#ECDDEA', borderRadius: 3, overflow: 'hidden' }, recordingFill: { height: '100%', borderRadius: 3, backgroundColor: '#B64E62' },
  waiting: { padding: 18, gap: 12, borderRadius: 18, backgroundColor: '#F7F3FD', flexDirection: 'row', alignItems: 'center' }, waitingText: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 23, color: COLORS.primaryDark },
  waitingLayout: { flexGrow: 1, justifyContent: 'center', paddingVertical: 20 },
  progressPanel: { padding: 16, gap: 16, borderRadius: 18, backgroundColor: '#F7F3FD' },
  reply: { gap: 14, paddingTop: 8 },
});
