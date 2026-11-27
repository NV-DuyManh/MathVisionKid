import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Platform, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { COLORS, FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { profileStyles as s } from './ProfileCards';
import { profileApi, type StarActivity } from './profileApi';

const PREVIEW_SIZE = 3;
const historyLabels = { LESSON: 'Hoàn thành bài học', QUIZ: 'Giải đúng Quiz', GAME: 'Thắng lượt chơi' };
const historyIcons = { LESSON: 'book-outline', QUIZ: 'checkmark-circle-outline', GAME: 'game-controller-outline' } as const;
type HistoryPage = Awaited<ReturnType<typeof profileApi.starHistory>>;
type PageRequest = { page: number };

export function StarHistory({ recent, style }: { recent: StarActivity[]; style?: StyleProp<ViewStyle> }) {
  const web = Platform.OS === 'web';
  const [request, setRequest] = useState<PageRequest>();
  const [result, setResult] = useState<{ request: PageRequest; data?: HistoryPage }>();
  useEffect(() => {
    if (!request) return;
    const call = new AbortController();
    void profileApi.starHistory(request.page, call.signal).then(data => {
      if (!call.signal.aborted) setResult({ request, data });
    }).catch(() => {
      if (!call.signal.aborted) setResult({ request });
    });
    return () => call.abort();
  }, [request]);

  const expanded = request !== undefined;
  const current = result?.request === request ? result : undefined;
  const loading = expanded && !current;
  const pagination = current?.data ?? (loading ? result?.data : undefined);
  const entries = expanded ? pagination?.entries ?? (loading ? recent.slice(0, PREVIEW_SIZE) : undefined)
    : web ? recent.slice(0, PREVIEW_SIZE) : recent;

  return <View style={[s.card, style]} testID="achievement-star-history">
    <Text accessibilityRole="header" style={s.heading}>Những lần em nhận sao</Text>
    {entries?.length === 0 && <Text style={s.body}>Sao sẽ xuất hiện khi em hoàn thành hoạt động đủ điều kiện.</Text>}
    {entries?.map((item, index) => {
      const key = item.completedAt + item.source + index;
      const date = new Date(item.completedAt).toLocaleDateString('vi-VN', web ? { timeZone: 'Asia/Ho_Chi_Minh' } : undefined);
      return web ? <View key={key} style={styles.historyRow} testID="star-history-entry">
        <View style={styles.historyIcon}><Ionicons name={historyIcons[item.source]} size={17} color={COLORS.primaryDark} accessible={false} /></View>
        <View style={styles.grow}><Text style={styles.titleName}>{historyLabels[item.source]}</Text><Text style={styles.titleDetail}>{date}</Text></View>
        <Text style={styles.historyStars}>+{item.stars} sao</Text>
      </View> : <Text key={key} style={s.body}>+{item.stars} sao · {historyLabels[item.source]} · {date}</Text>;
    })}
    {loading && <ActivityIndicator accessibilityLabel="Đang tải lịch sử nhận sao" />}
    {expanded && current && !pagination && <RecoveryNotice title="Chưa tải được lịch sử nhận sao" message="Em kiểm tra kết nối rồi thử lại nhé."
      actions={[{ label: 'Thử lại', onPress: () => setRequest({ page: request.page }) }]} />}
    {pagination && pagination.totalPages > 1 && <View style={styles.pagination}>
      <AppButton title="Trước" accessibilityLabel="Trang lịch sử trước" variant="secondary" disabled={loading || pagination.page <= 1}
        onPress={() => setRequest({ page: pagination.page - 1 })} />
      <Text style={styles.pageNumber} accessibilityLiveRegion="polite">Trang {pagination.page}/{pagination.totalPages}</Text>
      <AppButton title="Sau" accessibilityLabel="Trang lịch sử sau" variant="secondary" disabled={loading || pagination.page >= pagination.totalPages}
        onPress={() => setRequest({ page: pagination.page + 1 })} />
    </View>}
    {web && (expanded || recent.length > PREVIEW_SIZE) && <AppButton
      title={expanded ? 'Thu gọn' : 'Xem thêm'} accessibilityLabel={expanded ? 'Thu gọn lịch sử nhận sao' : 'Xem thêm lịch sử nhận sao'}
      variant="ghost" onPress={() => { setRequest(expanded ? undefined : { page: 1 }); setResult(undefined); }} />}
  </View>;
}

const styles = StyleSheet.create({
  historyRow: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 5, borderTopWidth: 1, borderColor: '#EEE8F7' },
  historyIcon: { backgroundColor: '#F1EAFF', borderRadius: 10, padding: 7 },
  grow: { flex: 1, minWidth: 0, gap: 2 },
  titleName: { color: COLORS.textPrimary, fontFamily: FONTS.extraBold, fontSize: 14, lineHeight: 18 },
  titleDetail: { color: STUDENT_WEB.muted, fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 17 },
  historyStars: { color: '#855100', backgroundColor: '#FFF3D5', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 5, fontFamily: FONTS.extraBold, fontSize: 12 },
  pagination: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 6 },
  pageNumber: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.primaryDark },
});
