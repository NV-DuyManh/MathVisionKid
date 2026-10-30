import React, { useCallback, useContext, useRef, useState } from 'react';
import { Image, Pressable, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { AuthContext } from '../../context/AuthContext';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { quizApi, Quiz, QuizGroup, QuizLibrary, quizError } from '../../features/quiz/quizApi';
import { quizStyles as s } from '../../features/quiz/quizStyles';

const GROUPS: { id: QuizGroup; title: string }[] = [{ id: 'PENDING', title: 'Chờ em làm' }, { id: 'IN_PROGRESS', title: 'Đang làm dở' }, { id: 'COMPLETED', title: 'Đã hoàn thành' }];
export default function QuizLibraryScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id || auth?.user?.userId;
  return owner ? <Library key={owner} /> : null;
}
function Library() {
  const router = useRouter();
  const [group, setGroup] = useState<QuizGroup>('PENDING'), [result, setResult] = useState<QuizLibrary | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [retry, setRetry] = useState(0);
  const [totalStars, setTotalStars] = useState<number | null>(null);
  const controller = useRef<AbortController | null>(null), active = useRef(false);
  useFocusEffect(useCallback(() => {
    void retry;
    active.current = true;
    const abort = new AbortController(); controller.current = abort;
    setBusy(true); setError(''); setResult(null); setTotalStars(null);
    void quizApi.list(group, 0, abort.signal).then(data => { if (active.current && !abort.signal.aborted) setResult(data); })
      .catch(failure => { if (active.current && !abort.signal.aborted) setError(quizError(failure)); })
      .finally(() => { if (active.current && !abort.signal.aborted) { setBusy(false); controller.current = null; } });
    void quizApi.count(abort.signal).then(data => { if (active.current && !abort.signal.aborted) setTotalStars(data.totalStars); }).catch(() => {});
    return () => { active.current = false; abort.abort(); controller.current?.abort(); controller.current = null; };
  }, [group, retry]));
  const more = async () => {
    if (!result || busy || controller.current) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError('');
    try {
      const next = await quizApi.list(group, result.page + 1, abort.signal);
      if (active.current && !abort.signal.aborted) setResult(previous => previous ? { ...next, items: [...previous.items, ...next.items] } : next);
    } catch (failure) { if (active.current && !abort.signal.aborted) setError(quizError(failure)); }
    finally { if (active.current && !abort.signal.aborted) { controller.current = null; setBusy(false); } }
  };
  const statusLabel = (quiz: Quiz) => {
    if (quiz.status === 'COMPLETED') {
      if (quiz.completedWithSolution) {
        return 'Hoàn thành với hướng dẫn – Không tính sao';
      }
      return `Đã hoàn thành · ${quiz.stars} sao`;
    }
    return quiz.status === 'IN_PROGRESS' ? 'Đang làm dở' : 'Chờ em làm';
  };
  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <AppHeader title="Quiz của em" showBack />
    <ScrollView style={s.scroll} contentContainerStyle={s.content}>
      <View style={s.card}><Text style={s.heading}>Mỗi câu đố, thêm một khám phá</Text><Text style={s.body}>Cùng Sao luyện lại điều em vừa học, theo nhịp của riêng em.</Text>
        {totalStars !== null ? <Text style={s.topic}>{totalStars > 0 ? `Em đã nhận ${totalStars} sao từ Quiz` : 'Em chưa nhận sao nào. Thử một Quiz để nhận sao nhé!'}</Text> : null}</View>
      <View style={s.groups}>{GROUPS.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityState={{ selected: group === item.id }} onPress={() => setGroup(item.id)}
        style={[s.group, group === item.id && s.selected]}><Text style={s.topic}>{item.title}</Text></Pressable>)}</View>
      {busy && !result ? <View style={s.card}><TaskProgress steps={['Mở thư viện của em', 'Tải các câu đố']} activeStep={1} /></View> : null}
      {error ? <View style={s.card}><Text accessibilityRole="alert" style={s.error}>{error}</Text><AppButton title="Thử lại" onPress={() => result ? void more() : setRetry(value => value + 1)} /></View> : null}
      {result && !result.items.length ? <View style={s.card}>
        <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={s.mascot} accessible={false} />
        <Text style={s.title}>{group === 'COMPLETED' ? 'Hành trình Quiz đang chờ em' : group === 'IN_PROGRESS' ? 'Em chưa có câu đố làm dở' : 'Chưa có câu đố đang chờ'}</Text>
        <Text style={s.body}>Sau khi học hoặc xem nhận xét bài làm, em chọn Hoàn tất để cùng Sao mở một câu tương tự nhé.</Text>
        <AppButton title="Về trang chủ" variant="secondary" onPress={() => router.replace('/(tabs)')} /></View> : null}
      {result?.items.map(quiz => <View key={quiz.quizId} style={s.card}>
        <Text style={s.topic}>{quiz.topicName}</Text><Text style={s.body}>{quiz.questionText}</Text>
        <Text style={s.small}>{new Date(quiz.createdAt).toLocaleDateString('vi-VN')} · {statusLabel(quiz)}</Text>
        <AppButton title={quiz.status === 'COMPLETED' ? 'Xem lại' : quiz.status === 'IN_PROGRESS' ? 'Tiếp tục' : 'Bắt đầu'} variant="secondary"
          onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} /></View>)}
      {result && result.page + 1 < result.totalPages ? <AppButton title="Xem thêm Quiz" variant="secondary" disabled={busy} loading={busy} onPress={() => void more()} /> : null}
    </ScrollView>
  </SafeAreaView>;
}
