import React, { useCallback, useContext, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { ProfileRankCard, ProfileStats, profileStyles as s, StudentAvatar } from '../../features/student-profile/ProfileCards';
import { profileApi, type Leaderboard } from '../../features/student-profile/profileApi';
import { useStudentProfile } from '../../features/student-profile/useStudentProfile';

export default function AchievementsScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  return <Achievements key={owner ?? 'signed-out'} owner={owner} />;
}

function Achievements({ owner }: { owner?: string }) {
  const router = useRouter();
  const profile = useStudentProfile(owner);
  const [classroom, setClassroom] = useState<string>();
  const [retry, setRetry] = useState(0);
  const [board, setBoard] = useState<{ classroom?: string; data?: Leaderboard; error?: boolean }>();
  useFocusEffect(useCallback(() => {
    if (!owner) return;
    const call = new AbortController();
    setBoard(undefined);
    void profileApi.leaderboard(classroom, call.signal).then(data => {
      if (!call.signal.aborted) setBoard({ classroom, data });
    }).catch(() => {
      if (!call.signal.aborted) setBoard({ classroom, error: true });
    });
    return () => call.abort();
    // The retry counter intentionally reloads the focused request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [owner, classroom, retry]));
  const current = board?.classroom === classroom ? board : undefined;
  const value = profile.value;
  return <SafeAreaView style={s.screen} edges={['top']}>
    <ScrollView contentContainerStyle={s.content}>
      <StudentPageHeader compact title="Thành tích" onBack={() => router.replace('/(tabs)')} onAvatar={() => router.push('/(tabs)/profile')} />
      {value ? <>
        <ProfileRankCard profile={value} />
        <ProfileStats profile={value} />
        <View style={s.card}>
          <Text accessibilityRole="header" style={s.heading}>Nhiệm vụ của em</Text>
          <Text style={s.body}>Hôm nay · {Math.min(1, value.stats.today)}/1 hoạt động</Text>
          <Text style={s.body}>7 ngày qua · {Math.min(5, value.stats.week)}/5 hoạt động</Text>
          <View style={s.row}>
            <AppButton title="Học một bài" onPress={() => router.push('/(tabs)/lessons')} />
            <AppButton title="Mở Quiz" variant="secondary" onPress={() => router.push('/quiz')} />
            <AppButton title="Chơi luyện toán" variant="secondary" onPress={() => router.push('/games/arithmetic-quest')} />
          </View>
        </View>
        <View style={s.card}>
          <Text accessibilityRole="header" style={s.heading}>Bộ sưu tập danh hiệu</Text>
          {value.titles.map(title => <View key={title.id} style={[s.row, s.chip]}>
            <Ionicons name={title.unlocked ? 'ribbon' : 'lock-closed-outline'} size={25} color="#5B339D" accessible={false} aria-hidden />
            <View style={{ flex: 1, minWidth: 150 }}>
              <Text style={s.heading}>{title.name}</Text>
              <Text style={s.body}>{title.rarity} · {title.unlocked ? 'Đã mở khóa' : `${title.progress}/${title.goal}`}</Text>
              <Text style={s.body}>{title.description}</Text>
            </View>
          </View>)}
          <AppButton title="Chọn danh hiệu trên hồ sơ" variant="secondary" onPress={() => router.push('/(tabs)/profile')} />
        </View>
        <View style={s.card}>
          <Text accessibilityRole="header" style={s.heading}>Những lần em nhận sao</Text>
          {value.history.length === 0 && <Text style={s.body}>Sao sẽ xuất hiện khi em hoàn thành hoạt động đủ điều kiện.</Text>}
          {value.history.map((item, index) => <Text key={item.completedAt + item.source + index} style={s.body}>
            +{item.stars} sao · {{ LESSON: 'Hoàn thành bài học', QUIZ: 'Giải đúng Quiz', GAME: 'Thắng lượt chơi' }[item.source]} · {new Date(item.completedAt).toLocaleDateString('vi-VN')}
          </Text>)}
        </View>
      </> : profile.failed ? <RecoveryNotice title="Chưa tải được thành tích" message="Em kiểm tra kết nối và thử lại nhé."
        actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại thành tích', icon: 'refresh-outline', onPress: profile.retry }]} />
        : <ActivityIndicator accessibilityLabel="Đang tải thành tích" />}
      <View style={s.card}>
        <Text accessibilityRole="header" style={s.heading}>Bảng xếp hạng</Text>
        <Text style={s.body}>Thách Đấu dành cho Top 200 toàn hệ thống đã đạt ít nhất Chiến Tướng.</Text>
        <View style={s.row}>{[{ id: undefined, name: 'Toàn hệ thống' }, ...(value?.classrooms ?? [])].map(scope =>
          <Pressable key={scope.id ?? 'all'} accessibilityRole="button" accessibilityState={{ selected: classroom === scope.id }}
            style={[s.chip, classroom === scope.id && s.selected]} onPress={() => setClassroom(scope.id)}><Text style={s.body}>{scope.name}</Text></Pressable>)}</View>
        {current?.error ? <RecoveryNotice title="Chưa mở được bảng xếp hạng" message="Em kiểm tra kết nối rồi thử lại nhé."
          actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại bảng xếp hạng', icon: 'refresh-outline', onPress: () => setRetry(n => n + 1) }]} />
          : current?.data ? <>
            <Text style={s.body}>{current.data.ownPosition ? `Vị trí của em · #${current.data.ownPosition}` : 'Em chưa có vị trí trên bảng này.'}</Text>
            {current.data.entries.length === 0 && <Text style={s.body}>Chưa có bạn nào được xếp hạng.</Text>}
            {current.data.entries.map(item => <View key={item.alias} style={[s.row, s.chip]}>
              <Text style={s.heading}>#{item.position}</Text><StudentAvatar id={item.avatar} size={32} />
              <View style={{ flex: 1, minWidth: 105 }}><Text style={s.body}>{item.alias}{item.self ? ' (em)' : ''}</Text><Text style={s.body}>{item.rank.name}</Text></View>
              <Text style={s.body}>{item.stars} sao</Text>
            </View>)}
          </> : <ActivityIndicator accessibilityLabel="Đang tải bảng xếp hạng" />}
      </View>
    </ScrollView>
  </SafeAreaView>;
}
