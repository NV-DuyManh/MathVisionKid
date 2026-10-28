import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { ActivityIndicator, AppState, Image, Keyboard, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import type { TextInputInstance } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
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
import { useNarrationPreparation } from './NarrationPreparation';
import { mediaTime } from './MediaTimeline';

type Props = { sessionId: string; revision: number; stepIndex: number; scope: string; onReturn?: () => void };
export function LessonQuestion(props: Props) {
  return <QuestionSession key={JSON.stringify([props.scope, props.sessionId, props.revision, props.stepIndex])} {...props} />;
}
function QuestionSession({ sessionId, revision, stepIndex, scope, onReturn }: Props) {
  const { recorder, durationMillis } = useQuestionRecorder();
  const [question, setQuestion] = useState(''), [reply, setReply] = useState<LessonReply | null>(null);
  const [phase, setPhase] = useState<'idle' | 'preparing' | 'recording' | 'transcribing' | 'asking' | 'stopping'>('idle');
  const [notice, setNotice] = useState('');
  const [transcriptionFailed, setTranscriptionFailed] = useState(false);
  const [transcribingStep, setTranscribingStep] = useState(0);
  const [recording, setRecording] = useState<{ uri: string; durationMillis: number } | null>(null);
  const [replayQuestion, setReplayQuestion] = useState(false), [inputFocused, setInputFocused] = useState(false);
  const questionInput = useRef<TextInputInstance>(null);
  const helperId = useId(), noticeId = useId(), replayId = useId();
  useNarrationPreparation(reply ? { sessionId, revision } : null, reply ? [reply.spokenExplanation, reply.followUp] : []);
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
  const transcribe = async (uri: string | null, id: number) => {
    const controller = new AbortController(); pending.current = controller;
    try {
      if (!uri) throw new Error('no recording');
      recordingUri.current = uri; setRecording({ uri, durationMillis: recordedDuration.current });
      setTranscribingStep(1);
      const text = await TutorService.transcribeQuestion(uri, controller.signal);
      if (active.current && id === generation.current) { setTranscriptionFailed(false); setQuestion(text); setReply(null); setNotice('Em đọc lại, sửa nếu cần rồi bấm Gửi câu hỏi.'); }
    } catch (failure: unknown) {
      if (active.current && id === generation.current) {
        const error = failure as { code?: string; response?: { status?: number } } | null;
        const status = error?.response?.status;
        setTranscriptionFailed(true);
        setNotice(error?.code === 'ERR_NETWORK' ? 'Chưa gửi được bản ghi. Em kiểm tra kết nối rồi thử lại bản ghi này nhé.'
          : error?.code === 'ECONNABORTED' || error?.code === 'ETIMEDOUT' ? 'Đã hết thời gian chuyển bản ghi thành chữ. Em có thể thử lại bản ghi này.'
          : status === 429 ? 'Em đã gửi nhiều bản ghi liên tiếp. Chờ một chút rồi thử lại bản ghi này nhé.'
          : status === 503 ? 'Phần chuyển giọng nói thành chữ đang chưa sẵn sàng. Bản ghi vẫn được giữ để em thử lại.'
          : 'Chưa nghe rõ lúc này. Em có thể thử lại bản ghi này, ghi lại hoặc gõ câu hỏi nhé.');
        if (__DEV__) console.warn('[question-transcription]', { status: Number.isInteger(status) ? status : 0,
          category: error?.code && /^[A-Z_]{1,40}$/.test(error.code) ? error.code : 'REQUEST_FAILED' });
      }
    } finally {
      if (active.current && id === generation.current) { busy.current = false; setPhase('idle'); }
    }
  };
  const finish = async () => {
    if (!ownedRecording.current) return;
    const id = generation.current;
    setTranscriptionFailed(false); setTranscribingStep(0); setPhase('transcribing'); const uri = await endRecording();
    if (!active.current || id !== generation.current) { clean(uri); return; }
    await transcribe(uri, id);
  };
  const retryTranscription = async () => {
    if (busy.current || !recordingUri.current) return;
    busy.current = true; const id = ++generation.current;
    setTranscriptionFailed(false); setNotice(''); setTranscribingStep(1); setPhase('transcribing');
    await transcribe(recordingUri.current, id);
  };
  const start = async () => {
    if (busy.current) return;
    busy.current = true; const id = ++generation.current; setNotice(''); setTranscriptionFailed(false); setReply(null); setReplayQuestion(false); setPhase('preparing');
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
    {reply ? <View style={styles.questionBubble}><View style={styles.inputHeading}><Text style={styles.smallLabel}>CÂU HỎI CỦA EM</Text>
      {recording ? <Pressable accessibilityRole="button" accessibilityLabel="Nghe lại câu hỏi đã gửi" accessibilityState={{ expanded: replayQuestion }} aria-expanded={replayQuestion} aria-controls={replayQuestion ? replayId : undefined} onPress={() => setReplayQuestion(value => !value)} style={styles.replayLink}><Ionicons name="volume-medium-outline" size={16} color="#7046DD" accessible={false}/><Text style={styles.replayText}>{replayQuestion ? 'Thu gọn' : 'Nghe lại'}</Text></Pressable> : null}</View>
      <MathText style={styles.body}>{question}</MathText>{replayQuestion && recording ? <View nativeID={replayId}><QuestionRecording uri={recording.uri} durationMillis={recording.durationMillis} /></View> : null}</View>
      : !waiting && phase !== 'recording' ? <View style={styles.welcome}><View style={styles.starBadge}><Image source={require('../../../assets/illustrations/mathvision-star.png')} resizeMode="contain" style={styles.star} accessible={false}/></View><View style={styles.flex}><Text style={styles.intro}>Em muốn hỏi chỗ nào?</Text><Text style={styles.caption}>Nói hoặc viết, mình cùng gỡ từng chút nhé.</Text></View></View> : null}
    {phase === 'recording' ? <View style={styles.recording}>
      <View style={styles.recordingHeading}><View style={styles.micBadge}><Ionicons name="mic" size={24} color="#A84255" accessible={false} /></View><View style={styles.recordingTitle}><Text style={styles.intro}>Mình đang nghe em</Text><Text style={styles.caption}>Nói xong, em bấm nút bên dưới nhé.</Text></View></View>
      <View style={styles.recordingTime}><View style={styles.recordingDot} /><Text style={styles.recordingLabel}>ĐANG GHI ÂM</Text><Text style={styles.timer}>{mediaTime(Math.min(30, durationMillis / 1000))} / 0:30</Text></View>
      <View accessibilityRole="progressbar" accessibilityLabel="Thời gian ghi âm" accessibilityValue={{ min: 0, max: 30, now: Math.min(30, Math.floor(durationMillis / 1000)) }} style={styles.recordingTrack}><View style={[styles.recordingFill, { width: `${Math.min(100, Math.max(0, durationMillis / 300))}%` }]} /></View>
      <AppButton title="Nói xong" onPress={() => { void finish(); }} />
    </View> : phase === 'idle' ? !reply ? <>
      {recording ? <QuestionRecording key={recording.uri} uri={recording.uri} durationMillis={recording.durationMillis} /> : null}
      <Pressable accessibilityRole="button" accessibilityLabel="Ghi âm câu hỏi" accessibilityHint="Mở micro để ghi câu hỏi, tối đa 30 giây" style={({ pressed }) => [styles.mic, pressed && { opacity: .8 }]} onPress={() => { void start(); }}>
        <LinearGradient colors={['#F1E9FF', '#F9F5FF']} start={{x:0,y:0}} end={{x:1,y:1}} style={[styles.micFill, recording && styles.micAgain]}>
          <View style={[styles.micCircle, recording && styles.micCircleSmall]}><Ionicons name={recording ? 'refresh' : 'mic'} size={recording ? 19 : 28} color="#FFFFFF" accessible={false}/></View>
          <View style={recording ? styles.flex : styles.micWords}><Text style={styles.label}>{recording ? 'Nói lại câu hỏi' : 'Chạm để nói câu hỏi'}</Text>{!recording ? <Text style={styles.caption}>Tối đa 30 giây · Em kiểm tra chữ trước khi gửi</Text> : null}</View>
        </LinearGradient></Pressable>
      <View style={styles.inputHeading}><Text style={styles.inputLabel}>{question ? 'Kiểm tra câu hỏi của em' : 'Hoặc viết câu hỏi'}</Text>{question.length > 400 ? <Text style={styles.count}>{question.length}/500</Text> : null}
        {question && recording ? <Pressable accessibilityRole="button" accessibilityLabel="Chỉnh sửa câu hỏi" onPress={() => questionInput.current?.focus()} style={styles.replayLink}><Ionicons name="create-outline" size={16} color="#7046DD" accessible={false}/><Text style={styles.replayText}>Sửa</Text></Pressable> : null}</View>
      <TextInput ref={questionInput} accessibilityLabel="Câu hỏi của em" aria-describedby={`${helperId}${notice ? ` ${noticeId}` : ''}`} value={question} onChangeText={setQuestion} maxLength={500} multiline style={[styles.input, inputFocused && styles.inputFocused]}
        onFocus={() => setInputFocused(true)} onBlur={() => setInputFocused(false)} placeholder="Ví dụ: Vì sao phải quy đồng?" placeholderTextColor={COLORS.textSecondary} />
      <Text nativeID={helperId} style={styles.caption}>{question.trim().length < 2 ? 'Em nhập câu hỏi hoặc dùng micro để bắt đầu nhé.' : 'Em có thể sửa câu hỏi trước khi gửi.'}</Text>
      <AppButton title="Gửi câu hỏi" disabled={question.trim().length < 2} onPress={() => { void ask(); }} />
    </> : null : phase === 'asking' || phase === 'transcribing' ? <View style={styles.progressPanel}>
      <Text style={styles.intro}>{phase === 'asking' ? 'Mình cùng tìm hiểu nhé' : 'Mình đang nghe lại câu hỏi'}</Text>
      <TaskProgress steps={phase === 'asking' ? ['Câu hỏi đã nhập', 'Soạn lời giải thích', 'Mở câu trả lời'] : ['Lưu câu hỏi vừa nói', 'Chuyển lời nói thành chữ', 'Mở phần kiểm tra']}
        key={phase} timeoutSeconds={45} activeStep={phase === 'asking' ? 1 : transcribingStep} />
    </View> : <View style={styles.waiting} accessibilityLiveRegion="polite" aria-busy><ActivityIndicator color={COLORS.primaryDark} /><Text style={styles.waitingText}>{phase === 'stopping' ? 'Đang dừng mic…' : 'Đang mở mic…'}</Text></View>}
    {phase !== 'idle' && phase !== 'stopping' ? <AppButton title={phase === 'recording' ? 'Hủy ghi âm' : 'Dừng'} variant="ghost" onPress={cancel} /> : null}
    {notice ? <View style={styles.notice}><Ionicons name="information-circle-outline" size={18} color="#765793" accessible={false}/><Text nativeID={noticeId} accessibilityLiveRegion="polite" style={styles.noticeText}>{notice}</Text></View> : null}
    {phase === 'idle' && transcriptionFailed && recording ? <AppButton title="Thử lại bản ghi này" variant="secondary" onPress={() => { void retryTranscription(); }} /> : null}
    {reply ? <View style={styles.reply} accessibilityLiveRegion="polite">
      <View style={styles.answerHeading}><Ionicons name="sparkles-outline" size={19} color="#8C68D1" accessible={false}/><Text style={styles.answerTitle}>Mình cùng tìm hiểu</Text></View><MathText style={styles.body}>{reply.answer}</MathText>
      {reply.followUp ? <View style={styles.followUp}><Text style={styles.smallLabel}>EM THỬ NGHĨ NHÉ</Text><MathText style={styles.body}>{reply.followUp}</MathText></View> : null}
      <LessonNarration compact scope={`${scope}:reply:${reply.answer}`} source={{ sessionId, revision }} paragraphs={[reply.spokenExplanation, reply.followUp]} />
      {onReturn ? <AppButton title="Em đã hiểu" variant="secondary" onPress={onReturn} /> : null}
      <AppButton title="Hỏi thêm chỗ này" variant="ghost" onPress={() => { setReply(null); setQuestion(''); setNotice(''); setReplayQuestion(false); clean(recordingUri.current); recordingUri.current = null; setRecording(null); }} />
    </View> : null}
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: 13 }, flex: { flex: 1, minWidth: 0 }, body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 14, lineHeight: 23 },
  intro: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 17, lineHeight: 25 },
  welcome: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 2 }, starBadge: { width: 46, height: 48, borderRadius: 16, backgroundColor: '#F3EDFF', overflow: 'hidden' }, star: { width: 46, height: 48 },
  questionBubble: { borderRadius: 20, backgroundColor: '#F6F2FC', padding: 14, gap: 6, borderWidth: 1, borderColor: '#EDE5F7' }, smallLabel: { fontFamily: FONTS.extraBold, fontSize: 10, lineHeight: 17, letterSpacing: .6, color: '#75598D' },
  answerHeading: { flexDirection: 'row', alignItems: 'center', gap: 7 }, answerTitle: { fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 24, color: '#3C2D56' },
  followUp: { borderRadius: 16, backgroundColor: '#EFF8F2', padding: 13, gap: 5 },
  caption: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 12, lineHeight: 19 },
  label: { fontFamily: FONTS.extraBold, color: COLORS.primaryDark, fontSize: 15, lineHeight: 23 },
  mic: { borderRadius: 22, overflow: 'hidden', borderWidth: 1, borderColor: '#E7DBFF' }, micFill: { padding: 18, alignItems: 'center', justifyContent: 'center', gap: 10 }, micWords: { alignItems: 'center', gap: 3 },
  micCircle: { width: 60, height: 60, borderRadius: 22, backgroundColor: '#7950E2', alignItems: 'center', justifyContent: 'center', borderWidth: 5, borderColor: '#DDCFFF' }, micCircleSmall: { width: 38, height: 38, borderRadius: 13, borderWidth: 0 }, micAgain: { flexDirection: 'row', padding: 10, gap: 10 },
  input: { minHeight: 100, borderRadius: 18, borderWidth: 1.5, borderColor: '#E2D9F0', padding: 13, fontFamily: FONTS.regular, fontSize: 14, lineHeight: 23, color: COLORS.textPrimary, textAlignVertical: 'top', backgroundColor: '#FCFAFF' }, inputFocused: { borderColor: '#8E68E4', backgroundColor: '#FFFFFF' },
  inputHeading: { flexDirection: 'row', alignItems: 'center', gap: 8 }, inputLabel: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, lineHeight: 23, color: COLORS.textPrimary }, count: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary, fontVariant: ['tabular-nums'] },
  replayLink: { minHeight: 44, marginLeft: 'auto', paddingHorizontal: 7, gap: 5, flexDirection: 'row', alignItems: 'center', justifyContent: 'center' }, replayText: { fontFamily: FONTS.bold, fontSize: 12, color: '#7046DD' },
  notice: { flexDirection: 'row', gap: 8, alignItems: 'flex-start', padding: 12, borderRadius: 14, backgroundColor: '#F7F3FC' }, noticeText: { flex: 1, fontFamily: FONTS.regular, fontSize: 12, lineHeight: 19, color: '#695478' },
  recording: { borderRadius: 24, backgroundColor: '#FFFAFC', borderWidth: 1, borderColor: '#F0DDE7', padding: 18, gap: 18 },
  recordingHeading: { flexDirection: 'row', alignItems: 'center', gap: 12 }, recordingTitle: { flex: 1, gap: 3 }, micBadge: { width: 46, height: 46, borderRadius: 16, backgroundColor: '#FBE9ED', alignItems: 'center', justifyContent: 'center' },
  recordingTime: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap' }, recordingDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#B64E62' }, recordingLabel: { fontFamily: FONTS.extraBold, fontSize: 10, letterSpacing: .6, color: '#9E465E' }, timer: { marginLeft: 'auto', fontFamily: FONTS.extraBold, fontSize: 21, color: '#8E3D50', fontVariant: ['tabular-nums'] },
  recordingTrack: { height: 5, backgroundColor: '#ECDDEA', borderRadius: 3, overflow: 'hidden' }, recordingFill: { height: '100%', borderRadius: 3, backgroundColor: '#B64E62' },
  waiting: { padding: 18, gap: 12, borderRadius: 18, backgroundColor: '#F7F3FD', flexDirection: 'row', alignItems: 'center' }, waitingText: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 23, color: COLORS.primaryDark },
  waitingLayout: { flexGrow: 1, justifyContent: 'center', paddingVertical: 20 },
  progressPanel: { padding: 18, gap: 16, borderRadius: 22, backgroundColor: '#F7F3FD', borderWidth: 1, borderColor: '#E9DFF7' },
  reply: { gap: 14, paddingTop: 8 },
});
