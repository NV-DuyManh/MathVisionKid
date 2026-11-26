import React, { useContext, useEffect, useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Redirect, useIsFocused, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AuthContext } from '../../context/AuthContext';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { ChallengeButton as AppButton, CHALLENGE_COLORS as C, ChallengeWebStyles, StarMedal } from '../../components/ui/ChallengeVisuals';
import { FONTS } from '../../constants/theme';
import { Ionicons } from '@expo/vector-icons';
import Animated, { FadeIn, ReduceMotion } from 'react-native-reanimated';
import { profileApi, type GameMode, type GameRun } from '../../features/student-profile/profileApi';
import { STAR_QUEST, TRAINING_CATALOG } from '../../features/training-games/catalog';
import { trainingAccess } from '../../features/training-games/identity';
import { tokenStorage } from '../../services/auth/tokenStorage';
import { StudentGameTimeGate } from '../../features/student-profile/StudentGameTimeGate';
import { isAxiosError } from 'axios';

const rewardMessages = {
  REPEAT: 'Hôm nay em đã nhận sao từ thử thách này. Kết quả lượt này vẫn được ghi nhận.',
  DAILY_LIMIT: 'Hôm nay em đã đạt giới hạn nhận sao. Ngày mai em có thể nhận thêm.',
  GAME_LIMIT: 'Hôm nay em đã nhận đủ sao từ các trò chơi. Ngày mai em có thể nhận thêm.',
  UNAVAILABLE: 'Tài khoản này chưa đủ điều kiện nhận sao.',
};

export default function ArithmeticQuestScreen() {
  const auth = useContext(AuthContext);
  const router = useRouter();
  const focused = useIsFocused();
  const { mode } = useLocalSearchParams<{ mode?: string }>();
  const access = trainingAccess(auth?.user, !!auth?.isAuthenticated);
  if (auth?.isLoading) return null;
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;
  if (access.kind !== 'student') return <Redirect href="/games" />;
  const training = TRAINING_CATALOG.find(item => item.id === mode);
  if (mode && !training) return <Redirect href="/games" />;
  const gameMode = training?.mode ?? 'ARITHMETIC_QUEST';
  if (!focused) return null;
  return <StudentGameTimeGate key={`${access.studentId}:${gameMode}`} onLeave={() => router.dismissTo('/games')}>
    <Quest mode={gameMode} />
  </StudentGameTimeGate>;
}

function Quest({ mode }: { mode: GameMode }) {
  const router = useRouter();
  const game = TRAINING_CATALOG.find(item => item.mode === mode) ?? STAR_QUEST;
  const title = mode === 'ARITHMETIC_QUEST' ? game.title : `${game.title} · Thử thách tính sao`;
  const [run, setRun] = useState<GameRun>();
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [expired, setExpired] = useState(false);
  const [busy, setBusy] = useState(false);
  const request = useRef<AbortController | null>(null);
  const identity = useRef<Promise<string | null> | null>(null);
  const [pending, setPending] = useState<number | null>(null);
  const [pageWidth, setPageWidth] = useState(0);
  useEffect(() => () => request.current?.abort(), []);

  const perform = async (operation: (signal: AbortSignal, session: string | null) => Promise<GameRun>) => {
    if (request.current) return;
    const call = new AbortController();
    request.current = call; setError(''); setBusy(true);
    try {
      const session = await (identity.current ??= tokenStorage.getSessionId());
      const next = await operation(call.signal, session);
      if (!call.signal.aborted) { setPending(null); setExpired(false); setRun(next); setInput(''); }
    } catch (failure) {
      if (call.signal.aborted) return;
      const code = isAxiosError(failure) ? failure.response?.data?.error?.code : undefined;
      if (code === 'GAME_EXPIRED' || code === 'GAME_NOT_FOUND') {
        setPending(null);
        setExpired(true);
        setError('Lượt chơi đã hết hạn hoặc không còn. Em có thể mở một lượt mới.');
      } else if (code === 'GAME_LIMIT') {
        setError('Hôm nay em đã chơi đủ lượt tính sao. Em có thể quay lại vào ngày mai.');
      } else if (code === 'GAME_NOT_AVAILABLE') {
        setError('Tài khoản này chưa mở được lượt chơi tính sao.');
      } else if (code === 'STUDENT_GAME_LIMIT') {
        setError('Đã hết giờ chơi hôm nay.');
      } else {
        setError('Chưa nhận được kết quả. Em kiểm tra kết nối rồi thử lại nhé.');
      }
    } finally {
      request.current = null;
      if (!call.signal.aborted) setBusy(false);
    }
  };
  const start = () => { void perform((signal, session) => profileApi.startGame(mode, signal, session)); };
  const sync = () => {
    if (run) void perform((signal, session) => profileApi.readGame(run.id, signal, session));
  };
  const submit = () => {
    if (!run || run.completed || request.current || expired) return;
    if (pending === null && !/^\d{1,4}$/.test(input.trim())) { setError('Em nhập đáp án bằng số nhé.'); return; }
    const answer = pending ?? Number(input);
    setPending(answer);
    void perform((signal, session) => profileApi.answer(run, answer, signal, session));
  };
  const reward = run?.rewardStatus;
  const wide = pageWidth >= 840;
  const completed = run?.completed === true;
  const desktopPlay = Platform.OS === 'web' && wide && !!run && !completed;
  const stage = run?.question ?? 0;
  const length = run?.length ?? 5;
  return <SafeAreaView style={s.screen} edges={['top', 'left', 'right', 'bottom']}>
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <ScrollView contentContainerStyle={[s.content, desktopPlay && s.playContent]} keyboardShouldPersistTaps="handled">
      <StudentPageHeader compact title={title} backLabel="Quay lại danh sách trò chơi" onBack={() => router.dismissTo('/games')} />
      <View onLayout={event => setPageWidth(event.nativeEvent.layout.width)} style={[s.workspace, desktopPlay && s.playWorkspace]} testID="quest-workspace" {...(Platform.OS === 'web' ? { dataSet: { challenge: 'true' } } : {})}>
      <ChallengeWebStyles />
      {!desktopPlay && <View style={[s.hero, wide && s.heroWide]}>
        <View style={s.heroCopy}>
          <Text style={s.eyebrow}>MỖI PHÉP TÍNH, MỘT BƯỚC TIẾN</Text>
          <Text accessibilityRole="header" style={[s.heroTitle, wide && s.heroTitleWide]}>{mode === 'ARITHMETIC_QUEST' ? 'Đường đua sao' : game.title}</Text>
          <Text style={s.heroBody}>{!run ? 'Năm chặng nhỏ. Một hành trình khám phá khả năng tính nhẩm của em.' : completed ? 'Mỗi lần thử là một bước tiến. Cùng nhìn lại hành trình của em nhé!' : 'Bình tĩnh suy nghĩ, rồi chinh phục từng chặng theo nhịp của em.'}</Text>
        </View>
        {wide && <StarMedal size={170} />}
      </View>}
      <View style={[s.trackCard, desktopPlay && s.playTrack]} testID="quest-track" accessibilityLabel={`Đã hoàn thành ${completed ? length : stage} trên ${length} chặng`}>
        <View style={s.trackHeading}><Text style={s.title}>Hành trình của em</Text><Text style={s.small}>{completed ? length : stage}/{length} chặng</Text></View>
        <View style={s.track}>
          <View style={s.trackLine} />
          {Array.from({ length }, (_, index) => {
            const passed = completed || index < stage;
            const current = !!run && !completed && index === stage;
            return <View key={index} style={s.checkpoint} testID={`quest-checkpoint-${index + 1}`} accessibilityLabel={`Chặng ${index + 1}: ${passed ? 'Đã hoàn thành' : current ? 'Đang thực hiện' : 'Chưa bắt đầu'}`}>
              <View style={[s.checkpointIcon, passed && s.passed, current && s.current]}><Ionicons name={passed ? 'checkmark' : 'star'} size={22} color={passed ? '#FFFFFF' : current ? '#18164C' : '#8A80AA'} accessible={false} /></View>
              <Text style={[s.checkpointText, current && { color: C.deepPurple }]}>Chặng {index + 1}</Text>
            </View>;
          })}
        </View>
      </View>
      <View style={[s.columns, wide && s.columnsWide]}>
      <View style={[s.card, wide && s.main, desktopPlay && s.playCard]}>
        {!run ? <>
          <View style={s.sectionIcon}><Ionicons name="flag-outline" size={26} color={C.deepPurple} accessible={false} /></View>
          <Text accessibilityRole="header" style={s.heading}>Sẵn sàng xuất phát?</Text>
          <Text style={s.body}>Câu hỏi được chọn theo khối lớp trong hồ sơ. Em chỉ cần tính nhẩm và nhập đáp án.</Text>
          <AppButton title={mode === 'ARITHMETIC_QUEST' ? 'Bắt đầu đường đua' : 'Bắt đầu hoặc học tiếp'} loadingTitle="Đang mở lượt chơi…" loading={busy} disabled={busy} onPress={start} icon={<Ionicons name="arrow-forward" size={20} color="#FFFFFF" accessible={false} />} />
          <Text style={s.small}>Nếu có lượt đang dở, em sẽ được học tiếp.</Text>
        </> : run.completed ? <>
          <View style={s.resultArt}><StarMedal size={116} /></View>
          <Text accessibilityRole="header" accessibilityLiveRegion="polite" style={s.heading}>{run.correct >= 4 ? 'Em đã vượt thử thách!' : 'Mình luyện thêm nhé!'}</Text>
          <View style={s.resultScore}><Text style={s.score}>{run.correct}<Text style={s.scoreTotal}>/{run.length}</Text></Text><Text style={s.body}>câu trả lời đúng</Text></View>
          <Text accessibilityLiveRegion="polite" style={s.reward}>{run.stars > 0 ? `Em nhận được ${run.stars} sao!` : 'Lượt này: 0 sao'}</Text>
          {run.correct >= 4 && run.stars === 0 && <Text accessibilityLiveRegion="polite" style={s.body}>
            {reward && reward !== 'AWARDED' ? rewardMessages[reward] : 'Lượt này đã được ghi nhận vào tiến độ của em.'}
          </Text>}
          {run.correct < 4 && <Text style={s.body}>Cần đúng ít nhất 4 câu để vượt thử thách. Kết quả lượt này đã được ghi nhận.</Text>}
          <AppButton title="Chơi lượt mới" loading={busy} disabled={busy} onPress={start} />
          <AppButton title="Xem thành tích" variant="secondary" onPress={() => router.push('/(tabs)/achievements')} />
        </> : <>
          <Animated.Text key={stage} entering={FadeIn.duration(220).reduceMotion(ReduceMotion.System)} style={s.stage}>Chặng {run.question + 1}/{run.length} · {run.correct} câu đúng</Animated.Text>
          <View style={[s.problem, desktopPlay && s.playProblem]}><Text style={s.problemLabel}>THỬ TÀI TÍNH NHẨM</Text><Text accessibilityRole="header" accessibilityLiveRegion="polite" style={[s.equation, !wide && s.equationCompact]}>{run.prompt}{run.prompt?.endsWith('?') ? '' : ' = ?'}</Text></View>
          <Text style={s.title}>Đáp án của em</Text>
          <TextInput accessibilityLabel="Đáp án" aria-describedby={error ? 'quest-error' : undefined} style={[s.input, desktopPlay && s.playInput]} keyboardType="number-pad" maxLength={4} value={input} placeholder="Nhập kết quả…" autoComplete="off" autoCorrect={false}
            editable={!busy && pending === null && !expired} onChangeText={setInput} onSubmitEditing={submit} />
          {expired ? <AppButton title="Mở lượt mới" disabled={busy} onPress={start} /> : <>
            <AppButton title={pending !== null ? 'Gửi lại đáp án' : 'Gửi đáp án'} loadingTitle="Đang kiểm tra…" loading={busy} disabled={busy} onPress={submit} />
            {error !== '' && pending !== null && <AppButton title="Kiểm tra lại lượt chơi" variant="secondary" disabled={busy} onPress={sync} />}
          </>}
        </>}
        {error !== '' && <Text nativeID="quest-error" accessibilityRole="alert" style={s.error}>{error}</Text>}
      </View>
      <View style={[s.aside, wide && s.sideColumn]}>
        <Text style={s.asideEyebrow}>{run ? 'TIẾN ĐỘ THẬT CỦA EM' : 'ĐÍCH ĐẾN HÔM NAY'}</Text>
        <View style={s.fact}><View style={s.factIcon}><Ionicons name="flag" size={22} color={C.deepPurple} accessible={false} /></View><View style={s.factCopy}><Text style={s.factValue}>{length} chặng</Text><Text style={s.small}>Từng câu hỏi, từng bước tiến</Text></View></View>
        <View style={s.fact}><View style={[s.factIcon, { backgroundColor: '#E5F5ED' }]}><Ionicons name="checkmark-done" size={23} color={C.green} accessible={false} /></View><View style={s.factCopy}><Text style={s.factValue}>{run ? `${run.correct} câu đúng` : 'Đúng ít nhất 4 câu'}</Text><Text accessibilityLiveRegion="polite" style={s.small}>{run ? `Đã ghi nhận ${completed ? length : stage} chặng` : 'Để vượt thử thách này'}</Text></View></View>
        <View style={s.rewardNote}><Ionicons name="star" size={22} color="#906112" accessible={false} /><Text style={s.rewardNoteText}>{completed ? `${run.stars} sao thực nhận trong lượt này` : 'Sao được cấp khi em đủ điều kiện thưởng. Mỗi lượt chơi đều là một lần luyện tập.'}</Text></View>
      </View>
      </View>
      </View>
    </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F7F7FC' },
  content: { width: '100%', maxWidth: 1180, alignSelf: 'center', padding: 16, paddingBottom: 40, gap: 20 },
  workspace: { gap: 20 },
  playContent: { paddingTop: 8, paddingBottom: 16, gap: 0 },
  playWorkspace: { gap: 12 },
  playTrack: { padding: 12, gap: 8 },
  playCard: { padding: 18, gap: 10 },
  playProblem: { padding: 14, gap: 4 },
  playInput: { minHeight: 54, padding: 10 },
  hero: { backgroundColor: C.ink, padding: 24, borderRadius: 26, gap: 16 },
  heroWide: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 36, paddingVertical: 18 },
  heroCopy: { flex: 1, minWidth: 0, gap: 12 },
  eyebrow: { color: C.yellow, fontFamily: FONTS.extraBold, fontSize: 11, lineHeight: 18, letterSpacing: 1.5 },
  heroTitle: { color: '#FFFFFF', fontFamily: FONTS.black, fontSize: 32, lineHeight: 40 },
  heroTitleWide: { fontSize: 42, lineHeight: 52 },
  heroBody: { color: '#E3DDF8', fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25, maxWidth: 550 },
  trackCard: { padding: 20, gap: 20, backgroundColor: '#FFFFFF', borderRadius: 22, borderWidth: 1, borderColor: C.line },
  trackHeading: { flexDirection: 'row', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' },
  track: { flexDirection: 'row', justifyContent: 'space-between', position: 'relative' },
  trackLine: { position: 'absolute', top: 21, left: 22, right: 22, height: 3, backgroundColor: C.line },
  checkpoint: { alignItems: 'center', gap: 8 },
  checkpointIcon: { height: 44, width: 44, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F0EDF7', borderWidth: 2, borderColor: '#FFFFFF' },
  passed: { backgroundColor: C.green }, current: { backgroundColor: C.yellow, borderColor: C.ink },
  checkpointText: { fontFamily: FONTS.bold, fontSize: 11, lineHeight: 16, color: '#706780' },
  columns: { gap: 20 }, columnsWide: { flexDirection: 'row', alignItems: 'flex-start' }, main: { flex: 1.9, minWidth: 0 }, sideColumn: { flex: 1, minWidth: 0 },
  card: { padding: 24, borderRadius: 24, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: C.line, gap: 18 },
  heading: { fontFamily: FONTS.extraBold, fontSize: 26, lineHeight: 35, color: C.ink },
  title: { fontFamily: FONTS.extraBold, fontSize: 17, lineHeight: 24, color: C.ink },
  body: { fontFamily: FONTS.regular, fontSize: 16, lineHeight: 26, color: C.textSecondary },
  small: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: C.textSecondary },
  sectionIcon: { width: 52, height: 52, borderRadius: 17, backgroundColor: C.lavender, alignItems: 'center', justifyContent: 'center' },
  aside: { padding: 22, gap: 22, borderWidth: 1, borderColor: C.line, borderRadius: 24, backgroundColor: '#FFFFFF' },
  asideEyebrow: { fontFamily: FONTS.extraBold, fontSize: 11, lineHeight: 18, letterSpacing: 1, color: C.deepPurple },
  fact: { flexDirection: 'row', alignItems: 'center', gap: 12 }, factCopy: { flex: 1, minWidth: 0, gap: 3 },
  factIcon: { width: 44, height: 44, borderRadius: 14, backgroundColor: C.lavender, alignItems: 'center', justifyContent: 'center' },
  factValue: { fontFamily: FONTS.extraBold, fontSize: 18, lineHeight: 26, color: C.ink },
  rewardNote: { flexDirection: 'row', gap: 10, padding: 14, backgroundColor: C.warm, borderRadius: 16 },
  rewardNoteText: { flex: 1, minWidth: 0, fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 21, color: '#77521B' },
  stage: { fontFamily: FONTS.bold, fontSize: 14, color: C.deepPurple, lineHeight: 22 },
  problem: { backgroundColor: '#F4F1FF', borderRadius: 20, padding: 24, alignItems: 'center', gap: 18 },
  problemLabel: { fontFamily: FONTS.extraBold, fontSize: 10, lineHeight: 17, letterSpacing: 1.2, color: C.deepPurple },
  equation: { fontFamily: FONTS.black, fontSize: 42, lineHeight: 56, color: C.ink, textAlign: 'center' },
  equationCompact: { fontSize: 30, lineHeight: 42 },
  input: { minHeight: 66, borderWidth: 2, borderColor: '#9B8DCC', borderRadius: 16, padding: 14, backgroundColor: '#FFFFFF', color: C.ink, fontFamily: FONTS.bold, fontSize: 24, textAlign: 'center' },
  error: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 23, color: C.errorText, backgroundColor: C.errorLight, padding: 14, borderRadius: 12 },
  resultArt: { alignItems: 'center' }, resultScore: { alignItems: 'center', gap: 2 },
  score: { fontFamily: FONTS.black, fontSize: 52, lineHeight: 62, color: C.ink }, scoreTotal: { fontSize: 28, color: '#8A80AA' },
  reward: { fontFamily: FONTS.extraBold, fontSize: 20, lineHeight: 29, color: C.deepPurple, textAlign: 'center' },
});
