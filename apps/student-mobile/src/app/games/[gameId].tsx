import React, { useContext, useCallback, useEffect } from 'react';
import { Redirect, Stack, useIsFocused, useLocalSearchParams, useRouter } from 'expo-router';
import { TRAINING_GAME_IDS, isTrainingGameId } from '@mathvisionkid/training-games';
import { AuthContext } from '../../context/AuthContext';
import { trainingAccess } from '../../features/training-games/identity';
import { trainingTrace } from '../../features/training-games/diagnostics';
import { GameFallback, GamePlayer } from '../../features/training-games/GamePlayer';
import { trainingScreenOptions } from '../../features/training-games/presentation';
import { TRAINING_CATALOG, supportsTrainingGrade } from '../../features/training-games/catalog';
import { cancelGameDisplay } from '../../features/training-games/GameDisplay';
import { IS_STUDENT_WEB } from '../../constants/theme';
import { primaryGrade } from '../../data/primaryMathLessons';
import { useStudentProfile } from '../../features/student-profile/useStudentProfile';
import { Text } from 'react-native';

export function generateStaticParams() { return TRAINING_GAME_IDS.map(gameId => ({ gameId })); }
export default function TrainingGameRoute() {
  const auth = useContext(AuthContext), router = useRouter(), focused = useIsFocused();
  const { gameId, playMode } = useLocalSearchParams<{ gameId: string; playMode?: string }>();
  const access = trainingAccess(auth?.user, !!auth?.isAuthenticated);
  const profile = useStudentProfile(IS_STUDENT_WEB && access.kind === 'student' ? access.studentId : undefined);
  useEffect(() => {
    if (focused && !auth?.isLoading && isTrainingGameId(gameId)) trainingTrace('route', { gameId, mode: access.kind });
  }, [focused, auth?.isLoading, gameId, access.kind]);
  const back = useCallback(() => {
    cancelGameDisplay();
    router.dismissTo('/games');
  }, [router]);
  if (auth?.isLoading) return null;
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;
  if (!isTrainingGameId(gameId)) return <GameFallback message="Trò chơi này chưa có trong danh sách của em." onBack={back} />;
  // A query parameter never grants access: both auth and the development policy
  // must independently allow a trial. A real student always keeps their UUID.
  if (access.kind === 'blocked') return <GameFallback message={access.message} onBack={back} />;
  if (access.kind === 'trial' && playMode !== 'trial') return <GameFallback message="Tài khoản này chỉ có thể chơi thử không lưu thành tích. Em trở về danh sách và chọn Chơi thử nhé." onBack={back} />;
  const trial = access.kind === 'trial';
  const studentId = access.kind === 'student' ? access.studentId : access.owner;
  const grade = IS_STUDENT_WEB ? (trial ? 5 : primaryGrade(profile.failed ? undefined : profile.value?.gradeLevel)) : undefined;
  const game = TRAINING_CATALOG.find(item => item.id === gameId);
  let content: React.ReactNode = null;
  if (focused) {
    if (IS_STUDENT_WEB && grade === undefined) {
      content = profile.value || profile.failed
        ? <GameFallback message="Chưa đọc được khối lớp trong Của em." onBack={back} onRetry={profile.retry} />
        : <Text accessibilityLiveRegion="polite">Đang tải khối lớp của em…</Text>;
    } else if (grade !== undefined && game && !supportsTrainingGrade(game.grades, grade)) {
      content = <GameFallback message={`Trò chơi này chưa có câu hỏi cho lớp ${grade}.`} onBack={back} />;
    } else {
      content = <GamePlayer key={`${studentId}:${gameId}:${grade}`} studentId={studentId} trial={trial} gameId={gameId} grade={grade} onExit={back} />;
    }
  }
  return <><Stack.Screen options={trainingScreenOptions(gameId)} />{content}</>;
}
