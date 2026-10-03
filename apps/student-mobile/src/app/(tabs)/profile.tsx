import React, { useCallback, useContext, useState } from 'react';
import { Alert, Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { AuthContext } from '../../context/AuthContext';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { loadLessons, SavedLesson } from '../../features/tutoring/learningHistory';
import { recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';

export default function ProfileScreen() {
  const router = useRouter();
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id || auth?.user?.userId || auth?.user?.email;
  const [lessons, setLessons] = useState<SavedLesson[]>([]);
  const [error, setError] = useState(false);
  useFocusEffect(useCallback(() => {
    let active = true;
    setLessons([]); setError(false);
    loadLessons(owner).then(items => { if (active) setLessons(items); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [owner]));
  const capture = () => {
    recognitionDraftStore.clearDraft();
    router.push({ pathname: '/camera', params: { mode: 'MATH_TUTOR' } });
  };
  return <SafeAreaView style={styles.screen} edges={['top']}>
    <AppHeader title="Góc học tập của em" />
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <LinearGradient colors={['#F0E9FF', '#FAF7FF']} style={styles.identity}>
        <Image source={require('../../../assets/illustrations/student-avatar.png')} style={styles.avatar} resizeMode="contain" accessible={false} />
        <View style={styles.copy}><Text style={styles.name}>{auth?.user?.name || 'Chào em!'}</Text>
          <Text style={styles.body}>{auth?.user?.grade ? `Học sinh lớp ${auth.user.grade}` : 'Mỗi ngày, học thêm một điều mới.'}</Text></View>
      </LinearGradient>
      <View style={styles.row}><Text style={styles.heading}>Bài đã lưu</Text><Text style={styles.caption}>{lessons.length} bài</Text></View>
      <Text style={styles.body}>Giữ lại điều em đã nghĩ, rồi quay lại học tiếp.</Text>
      {error ? <Text style={styles.error}>Chưa mở được bài đã lưu. Em quay lại màn hình này để thử lại nhé.</Text>
        : lessons.length ? lessons.map(lesson => <Pressable key={lesson.id} accessibilityRole="button"
          accessibilityLabel={`Học tiếp: ${(lesson.problemText || lesson.workText).slice(0, 60)}`}
          onPress={() => router.push({ pathname: '/learning/math-guide', params: { problemText: lesson.problemText, workText: lesson.workText, lessonId: lesson.id, reflection: lesson.reflection } })}
          style={({ pressed }) => [styles.lesson, pressed && styles.pressed]}>
          <View style={styles.row}><View style={styles.label}><Ionicons name="book-outline" size={16} color={COLORS.primaryDark} accessible={false} />
            <Text style={styles.labelText}>CÙNG HỌC TIẾP</Text></View><Text style={styles.caption}>{new Date(lesson.timestamp).toLocaleDateString('vi-VN')}</Text></View>
          <Text style={styles.lessonTitle} numberOfLines={3}>{lesson.problemText || lesson.workText}</Text>
          {lesson.reflection ? <Text style={styles.body} numberOfLines={2}>Em đã nghĩ: {lesson.reflection}</Text> : null}
          <View style={styles.row}><Text style={styles.link}>Mở bài học</Text><Ionicons name="arrow-forward" size={19} color={COLORS.primaryDark} accessible={false} /></View>
        </Pressable>) : <View style={styles.empty}>
          <Image source={require('../../../assets/illustrations/saved-folder.png')} style={styles.art} resizeMode="contain" accessible={false} />
          <Text style={styles.heading}>Bắt đầu bộ sưu tập bài học</Text>
          <Text style={styles.centerBody}>Chụp bài toán, cùng suy nghĩ từng bước rồi lưu bài để học tiếp nhé.</Text>
          <AppButton title="Chụp bài toán" onPress={capture} />
        </View>}
      <View style={styles.info}><Ionicons name="shield-checkmark-outline" size={22} color={COLORS.primaryDark} accessible={false} />
        <Text style={styles.infoText}>Bài học được lưu theo tài khoản trên thiết bị này. Góc học tập chỉ giữ nội dung bài và suy nghĩ của em.</Text></View>
      <AppButton title="Đăng xuất" variant="ghost" onPress={() => Alert.alert('Đăng xuất', 'Em muốn đăng xuất khỏi tài khoản này?', [
        { text: 'Ở lại', style: 'cancel' }, { text: 'Đăng xuất', onPress: () => auth?.logout() },
      ])} />
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 20, paddingBottom: 116, width: '100%', maxWidth: 620, alignSelf: 'center', gap: 16 },
  identity: { flexDirection: 'row', alignItems: 'center', gap: 16, padding: 20, borderRadius: 28 },
  avatar: { width: 76, height: 76 }, copy: { flex: 1 },
  name: { fontFamily: FONTS.extraBold, fontSize: 24, color: COLORS.textPrimary, marginBottom: 6 },
  heading: { fontFamily: FONTS.extraBold, fontSize: 21, color: COLORS.textPrimary },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary },
  caption: { fontFamily: FONTS.semiBold, fontSize: 12, color: COLORS.textMuted },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 },
  lesson: { borderRadius: 25, backgroundColor: COLORS.surface, padding: 20, gap: 15, ...SHADOWS.small },
  label: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  labelText: { fontFamily: FONTS.extraBold, fontSize: 10, color: COLORS.primaryDark, letterSpacing: .7 },
  lessonTitle: { fontFamily: FONTS.bold, fontSize: 17, lineHeight: 26, color: COLORS.textPrimary },
  link: { fontFamily: FONTS.extraBold, fontSize: 14, color: COLORS.primaryDark },
  empty: { alignItems: 'center', padding: 23, borderRadius: 28, backgroundColor: '#F0EBFC', gap: 15 },
  art: { width: 106, height: 100 }, centerBody: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary, textAlign: 'center' },
  info: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 16, borderRadius: 20, backgroundColor: '#EAF6F0' },
  infoText: { flex: 1, fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: '#37644E' },
  error: { fontFamily: FONTS.regular, fontSize: 14, color: COLORS.errorText }, pressed: { opacity: .7 },
});
