import React, { useContext, useCallback, useEffect } from 'react';
import { Redirect, Stack, useIsFocused, useLocalSearchParams, useRouter } from 'expo-router';
import { TRAINING_GAME_IDS, isTrainingGameId } from '@mathvisionkid/training-games';
import { AuthContext } from '../../context/AuthContext';
import { trainingAccess } from '../../features/training-games/identity';
import { trainingTrace } from '../../features/training-games/diagnostics';
import { GameFallback, GamePlayer } from '../../features/training-games/GamePlayer';
import { trainingScreenOptions } from '../../features/training-games/presentation';

export function generateStaticParams() { return TRAINING_GAME_IDS.map(gameId => ({ gameId })); }
export default function TrainingGameRoute() {
  const auth = useContext(AuthContext), router = useRouter(), focused = useIsFocused();
  const { gameId, playMode } = useLocalSearchParams<{ gameId: string; playMode?: string }>();
  const access = trainingAccess(auth?.user, !!auth?.isAuthenticated);
  useEffect(() => {
    if (focused && !auth?.isLoading && isTrainingGameId(gameId)) trainingTrace('route', { gameId, mode: access.kind });
  }, [focused, auth?.isLoading, gameId, access.kind]);
  const back = useCallback(() => router.dismissTo('/games'), [router]);
  if (auth?.isLoading) return null;
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;
  if (!isTrainingGameId(gameId)) return <GameFallback message="Trò chơi này chưa có trong danh sách của em." onBack={back} />;
  // A query parameter never grants access: both auth and the development policy
  // must independently allow a trial. A real student always keeps their UUID.
  if (access.kind === 'blocked') return <GameFallback message={access.message} onBack={back} />;
  if (access.kind === 'trial' && playMode !== 'trial') return <GameFallback message="Tài khoản này chỉ có thể chơi thử không lưu thành tích. Em trở về danh sách và chọn Chơi thử nhé." onBack={back} />;
  const trial = access.kind === 'trial';
  const studentId = access.kind === 'student' ? access.studentId : access.owner;
  return <><Stack.Screen options={trainingScreenOptions(gameId)} />{focused && <GamePlayer key={`${studentId}:${gameId}`} studentId={studentId} trial={trial} gameId={gameId} onExit={back} />}</>;
}
