import React, { useContext, useEffect, useRef, useState } from 'react';
import { ScrollView, Text, TextInput, View } from 'react-native';
import { Redirect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AuthContext } from '../../context/AuthContext';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { AppButton } from '../../components/ui/AppButton';
import { profileStyles as s } from '../../features/student-profile/ProfileCards';
import { profileApi, type GameRun } from '../../features/student-profile/profileApi';

export default function ArithmeticQuestScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  if (auth?.isLoading) return null;
  if (!auth?.isAuthenticated || !owner) return <Redirect href="/login" />;
  return <Quest key={owner} />;
}

function Quest() {
  const router = useRouter();
  const [run, setRun] = useState<GameRun>();
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);

  const perform = async (operation: (signal: AbortSignal) => Promise<GameRun>) => {
    if (request.current) return;
    const call = new AbortController();
    request.current = call; setError(''); setBusy(true);
    try {
      const next = await operation(call.signal);
      if (!call.signal.aborted) { setRun(next); setInput(''); }
    } catch {
      if (!call.signal.aborted) setError('Chưa tiếp tục được lượt chơi. Em kiểm tra kết nối rồi thử lại hoặc mở lại lượt chơi.');
    } finally {
      request.current = null;
      if (!call.signal.aborted) setBusy(false);
    }
  };
  const submit = () => {
    if (!run || run.completed) return;
    if (!/^\d{1,4}$/.test(input.trim())) { setError('Em nhập đáp án bằng số nhé.'); return; }
    void perform(signal => profileApi.answer(run, Number(input), signal));
  };
  return <SafeAreaView style={s.screen} edges={['top']}>
    <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
      <StudentPageHeader compact title="Đường đua sao" onBack={() => router.dismissTo('/games')} />
      <View style={s.card}>
        {!run ? <>
          <Text accessibilityRole="header" style={s.heading}>Vượt 5 chặng tính nhẩm</Text>
          <Text style={s.body}>Giải đúng ít nhất 4 phép tính để hoàn thành thử thách. Em có thể nhận sao nếu còn lượt thưởng hôm nay.</Text>
          <AppButton title={busy ? 'Đang mở lượt chơi' : 'Bắt đầu hoặc học tiếp'} disabled={busy} onPress={() => { void perform(profileApi.startGame); }} />
        </> : run.completed ? <>
          <Text accessibilityRole="header" accessibilityLiveRegion="polite" style={s.heading}>{run.correct >= 4 ? 'Em đã vượt thử thách!' : 'Mình luyện thêm nhé!'}</Text>
          <Text style={s.body}>Em trả lời đúng {run.correct}/{run.length} câu.</Text>
          {run.stars > 0 && <Text accessibilityLiveRegion="polite" style={s.heading}>Em nhận được {run.stars} sao!</Text>}
          <AppButton title="Chơi lượt mới" disabled={busy} onPress={() => { void perform(profileApi.startGame); }} />
          <AppButton title="Xem thành tích" variant="secondary" onPress={() => router.push('/(tabs)/achievements')} />
        </> : <>
          <Text style={s.body}>Chặng {run.question + 1}/{run.length} · {run.correct} câu đúng</Text>
          <Text accessibilityRole="header" accessibilityLiveRegion="polite" style={s.heading}>{run.prompt} = ?</Text>
          <TextInput accessibilityLabel="Đáp án" style={s.input} keyboardType="number-pad" maxLength={4} value={input}
            editable={!busy} onChangeText={setInput} onSubmitEditing={submit} />
          <AppButton title={busy ? 'Đang kiểm tra' : 'Gửi đáp án'} disabled={busy} onPress={submit} />
          {error !== '' && <AppButton title="Mở lại lượt chơi" variant="secondary" disabled={busy} onPress={() => { void perform(profileApi.startGame); }} />}
        </>}
        {error !== '' && <Text accessibilityRole="alert" style={s.error}>{error}</Text>}
      </View>
    </ScrollView>
  </SafeAreaView>;
}
