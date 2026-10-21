import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AppState, Keyboard, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { File } from 'expo-file-system';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { LessonReply, TutorService } from './api/TutorService';
import { LessonNarration } from './LessonNarration';
import { useQuestionRecorder } from './useQuestionRecorder';

export function LessonQuestion({ sessionId, revision, stepIndex, scope }: { sessionId: string; revision: number; stepIndex: number; scope: string }) {
  const { recorder, durationMillis } = useQuestionRecorder();
  const [question, setQuestion] = useState(''), [reply, setReply] = useState<LessonReply | null>(null);
  const [phase, setPhase] = useState<'idle' | 'preparing' | 'recording' | 'transcribing' | 'asking' | 'stopping'>('idle');
  const [notice, setNotice] = useState(''), [consentOpen, setConsentOpen] = useState(false);
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
    void endRecording().then(clean).finally(() => {
      stopping.current = false;
      if (active.current && id === generation.current) { busy.current = false; setPhase('idle'); setNotice('Đã dừng. Em có thể gõ câu hỏi.'); }
    });
  }, [endRecording]);
  useEffect(() => {
    active.current = true;
    const listener = AppState.addEventListener('change', state => { if (state !== 'active') cancel(); });
    return () => { active.current = false; listener.remove(); cancel(); };
  }, [scope, cancel]);
  const finish = async () => {
    if (!ownedRecording.current) return;
    const id = generation.current;
    setPhase('transcribing'); const uri = await endRecording();
    if (!active.current || id !== generation.current) { clean(uri); return; }
    const controller = new AbortController(); pending.current = controller;
    try {
      if (!uri) throw new Error('no recording');
      const text = await TutorService.transcribeQuestion(uri, controller.signal);
      if (active.current && id === generation.current) { setQuestion(text); setReply(null); setNotice('Em đọc lại, sửa nếu cần rồi bấm Gửi câu hỏi.'); }
    } catch {
      if (active.current && id === generation.current) setNotice('Chưa nghe rõ lúc này. Em thử ghi lại hoặc gõ câu hỏi nhé.');
    } finally {
      clean(uri);
      if (active.current && id === generation.current) { busy.current = false; setPhase('idle'); }
    }
  };
  const start = async () => {
    if (busy.current) return;
    busy.current = true; const id = ++generation.current; setNotice(''); setReply(null); setPhase('preparing');
    try {
      await recorder.prepare();
      if (!active.current || id !== generation.current) { clean(await recorder.stop()); return; }
      ownedRecording.current = true; recorder.start(() => { void finish(); });
      setPhase('recording'); setConsentOpen(false); setReply(null);
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
  return <View style={styles.stack}>
    {reply ? <><Text style={styles.label}>Câu hỏi của em</Text><MathText style={styles.body}>{question}</MathText></>
      : <Text style={styles.body}>Em hỏi về chỗ chưa hiểu trong bước đang học. Mình cùng tìm cách làm nhé.</Text>}
    {phase === 'recording' ? <View style={styles.recording}>
      <Ionicons name="mic" size={30} color={COLORS.primaryDark} /><Text style={styles.label}>Đang nghe em · {Math.min(30, Math.floor(durationMillis / 1000))}/30 giây</Text>
      <AppButton title="Nói xong" onPress={() => { void finish(); }} />
    </View> : phase === 'idle' ? !reply ? <>
      {!consentOpen ? <Pressable accessibilityRole="button" accessibilityLabel="Ghi âm câu hỏi" style={styles.mic} onPress={() => setConsentOpen(true)}>
        <Ionicons name="mic-outline" size={25} color={COLORS.primaryDark} /><Text style={styles.label}>Nhấn để nói câu hỏi</Text></Pressable> : <View style={styles.recording}>
        <Text style={styles.body}>Bản ghi tối đa 30 giây sẽ được gửi để chuyển thành chữ khi em nói xong. Em không đọc tên đầy đủ, địa chỉ hay thông tin riêng nhé.</Text>
        <AppButton title="Đồng ý và ghi âm" onPress={() => { void start(); }} />
      </View>}
      <Text style={styles.label}>{question ? 'Kiểm tra câu hỏi của em' : 'Hoặc gõ câu hỏi'}</Text>
      <TextInput accessibilityLabel="Câu hỏi của em" value={question} onChangeText={setQuestion} maxLength={500} multiline style={styles.input}
        placeholder="Ví dụ: Vì sao phải quy đồng?" placeholderTextColor={COLORS.textSecondary} />
      <AppButton title="Gửi câu hỏi" disabled={question.trim().length < 2} onPress={() => { void ask(); }} />
    </> : null : <Text style={styles.label} accessibilityLiveRegion="polite">{phase === 'stopping' ? 'Đang dừng mic…' : phase === 'preparing' ? 'Đang mở mic…' : phase === 'asking' ? 'Mình đang đọc câu hỏi của em…' : 'Đang chuyển lời nói thành chữ…'}</Text>}
    {phase !== 'idle' && phase !== 'stopping' ? <AppButton title="Dừng" variant="secondary" onPress={cancel} /> : null}
    {notice ? <Text accessibilityLiveRegion="polite" style={styles.body}>{notice}</Text> : null}
    {reply ? <View style={styles.reply} accessibilityLiveRegion="polite">
      <Text style={styles.label}>Cùng hiểu chỗ này</Text><MathText style={styles.body}>{reply.answer}</MathText>
      {reply.followUp ? <MathText style={styles.label}>{reply.followUp}</MathText> : null}
      <LessonNarration compact scope={`${scope}:reply:${reply.answer}`} paragraphs={[reply.spokenExplanation, reply.followUp]} />
      <AppButton title="Hỏi thêm chỗ này" variant="ghost" onPress={() => { setReply(null); setQuestion(''); setNotice(''); }} />
    </View> : null}
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: 16 }, body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 16, lineHeight: 25 },
  label: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 16, lineHeight: 24 },
  mic: { minHeight: 60, borderRadius: 18, padding: 16, backgroundColor: '#F1ECFF', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  input: { minHeight: 110, borderRadius: 16, borderWidth: 1.5, borderColor: '#D6CDEF', padding: 15, fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25, color: COLORS.textPrimary, textAlignVertical: 'top' },
  recording: { borderRadius: 18, backgroundColor: '#F4F0FF', padding: 18, gap: 14 }, reply: { gap: 14, paddingTop: 8 },
});
