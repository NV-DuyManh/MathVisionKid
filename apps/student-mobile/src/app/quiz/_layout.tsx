import React, { useContext } from 'react';
import { Redirect, Stack } from 'expo-router';
import { Text, View } from 'react-native';
import { AuthContext } from '../../context/AuthContext';
import { quizStyles as s } from '../../features/quiz/quizStyles';
export default function QuizLayout() {
  const auth = useContext(AuthContext);
  if (auth?.isLoading) return <View style={[s.screen, s.content]}><Text style={s.body}>Đang mở Quiz của em…</Text></View>;
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}
