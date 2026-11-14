import React, { useContext, useEffect, useRef, useState } from 'react';
import { ScrollView, Text, TextInput, View } from 'react-native';
import { Redirect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AuthContext } from '../../context/AuthContext';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { AppButton } from '../../components/ui/AppButton';
import { profileStyles as s } from '../../features/student-profile/ProfileCards';
import { profileApi, type GameMode, type GameRun } from '../../features/student-profile/profileApi';
import { STAR_QUEST, TRAINING_CATALOG } from '../../features/training-games/catalog';
import { GameIcon } from '../../features/training-games/GameIcon';
import { trainingAccess } from '../../features/training-games/identity';
import { tokenStorage } from '../../services/auth/tokenStorage';
import { isAxiosError } from 'axios';

const rewardMessages = {
  REPEAT: 'Hôm nay em đã nhận sao từ thử thách này. Kết quả lượt này vẫn được ghi nhận.',
  DAILY_LIMIT: 'Hôm nay em đã đạt giới hạn nhận sao. Ngày mai em có thể nhận thêm.',
  GAME_LIMIT: 'Hôm nay em đã nhận đủ sao từ các trò chơi. Ngày mai em có thể nhận thêm.',
  UNAVAILABLE: 'Tài khoản này chưa đủ điều kiện nhận sao.',
};

export default function ArithmeticQuestScreen() {
  const auth = useContext(AuthContext);
  const { mode } = useLocalSearchParams<{ mode?: string }>();
  const access = trainingAccess(auth?.user, !!auth?.isAuthenticated);
  if (auth?.isLoading) return null;
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;
  if (access.kind !== 'student') return <Redirect href="/games" />;
  const training = TRAINING_CATALOG.find(item => item.id === mode);
  if (mode && !training) return <Redirect href="/games" />;
  const gameMode = training?.mode ?? 'ARITHMETIC_QUEST';
  return <Quest key={`${access.studentId}:${gameMode}`} mode={gameMode} />;
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
  return <SafeAreaView style={s.screen} edges={['top', 'left', 'right', 'bottom']}>
    <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
      <StudentPageHeader compact title={title} backLabel="Quay lại danh sách trò chơi" onBack={() => router.dismissTo('/games')} />
      <View style={s.card}>
        {!run ? <>
          <GameIcon artwork={game.artwork} />
          <Text accessibilityRole="header" style={s.heading}>{mode === 'ARITHMETIC_QUEST' ? 'Vượt 5 chặng tính nhẩm' : 'Vượt 5 câu hỏi toán'}</Text>
          <Text style={s.body}>Giải đúng ít nhất 4 câu để hoàn thành thử thách. Em có thể nhận sao nếu còn lượt thưởng hôm nay.</Text>
          <Text style={s.body}>Câu hỏi tính sao được chọn theo khối lớp trong hồ sơ của em.</Text>
          <AppButton title={busy ? 'Đang mở lượt chơi' : 'Bắt đầu hoặc học tiếp'} disabled={busy} onPress={start} />
        </> : run.completed ? <>
          <GameIcon artwork={game.artwork} />
          <Text accessibilityRole="header" accessibilityLiveRegion="polite" style={s.heading}>{run.correct >= 4 ? 'Em đã vượt thử thách!' : 'Mình luyện thêm nhé!'}</Text>
          <Text style={s.body}>Em trả lời đúng {run.correct}/{run.length} câu.</Text>
          {run.stars > 0 && <Text accessibilityLiveRegion="polite" style={s.heading}>Em nhận được {run.stars} sao!</Text>}
          {run.correct >= 4 && run.stars === 0 && <Text accessibilityLiveRegion="polite" style={s.body}>
            {reward && reward !== 'AWARDED' ? rewardMessages[reward] : 'Lượt này đã được ghi nhận vào tiến độ của em.'}
          </Text>}
          <AppButton title="Chơi lượt mới" disabled={busy} onPress={start} />
          <AppButton title="Xem thành tích" variant="secondary" onPress={() => router.push('/(tabs)/achievements')} />
        </> : <>
          <Text style={s.body}>Chặng {run.question + 1}/{run.length} · {run.correct} câu đúng</Text>
          <Text accessibilityRole="header" accessibilityLiveRegion="polite" style={s.heading}>{run.prompt}{run.prompt?.endsWith('?') ? '' : ' = ?'}</Text>
          <TextInput accessibilityLabel="Đáp án" style={s.input} keyboardType="number-pad" maxLength={4} value={input}
            editable={!busy && pending === null && !expired} onChangeText={setInput} onSubmitEditing={submit} />
          {expired ? <AppButton title="Mở lượt mới" disabled={busy} onPress={start} /> : <>
            <AppButton title={busy ? 'Đang kiểm tra' : pending !== null ? 'Gửi lại đáp án' : 'Gửi đáp án'} disabled={busy} onPress={submit} />
            {error !== '' && pending !== null && <AppButton title="Kiểm tra lại lượt chơi" variant="secondary" disabled={busy} onPress={sync} />}
          </>}
        </>}
        {error !== '' && <Text accessibilityRole="alert" style={s.error}>{error}</Text>}
      </View>
    </ScrollView>
  </SafeAreaView>;
}
