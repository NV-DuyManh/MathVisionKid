import React, { useContext } from 'react';
import { ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { AppButton } from '../../components/ui/AppButton';
import { AppHeader } from '../../components/ui/AppHeader';
import { AuthContext } from '../../context/AuthContext';
import { QuizInvitation } from '../../features/quiz/QuizInvitation';
import { quizStyles as s } from '../../features/quiz/quizStyles';

export default function QuizFromLearningScreen() {
  const { sourceType, sourceId } = useLocalSearchParams<{ sourceType?: string; sourceId?: string }>();
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id || auth?.user?.userId;
  const router = useRouter();
  if (!owner) return null;

  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <AppHeader title="Quiz sau bài học" showBack />
    <ScrollView style={s.scroll} contentContainerStyle={[s.content, s.workContent]}>
      {(sourceType === 'LESSON' || sourceType === 'WORK_REVIEW') && typeof sourceId === 'string' && sourceId.trim() && sourceId.length <= 100
        ? <QuizInvitation key={owner} sourceType={sourceType} sourceId={sourceId} />
        : <View style={s.card}><Text style={s.body}>Em mở Quiz từ bài vừa hoàn thành nhé.</Text></View>}
      <AppButton title="Về trang chủ" variant="ghost" onPress={() => router.replace('/(tabs)')} />
    </ScrollView>
  </SafeAreaView>;
}
