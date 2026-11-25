import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { LessonSheet } from '../tutoring/LessonSheet';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { profileApi, type RankMilestone, type StudentProfile } from './profileApi';
import { RankEmblem } from './RankEmblem';
import { profileStyles as s } from './ProfileCards';
import { FONTS } from '../../constants/theme';

export function RankStarProgress({ earned, goal }: { earned?: number; goal: number }) {
  if (!Number.isSafeInteger(goal) || goal <= 0) return null;
  const filled = Math.max(0, Math.min(goal, Math.floor(earned ?? 0)));
  const known = earned !== undefined;
  return <View testID="rank-star-progress" style={styles.starProgress}
    accessibilityRole={known ? 'progressbar' : undefined}
    accessibilityLabel={known ? 'Tiến độ sao trong bậc' : 'Số sao cần để lên bậc'}
    accessibilityValue={known ? { min: 0, max: goal, now: filled } : undefined}>
    {goal <= 5 ? <View style={styles.starSlots} aria-hidden accessibilityElementsHidden>
      {Array.from({ length: goal }, (_, index) => {
        const lit = index < filled;
        return <View key={index} testID={lit ? 'rank-star-filled' : 'rank-star-empty'}
          style={[styles.starSlot, lit && styles.starSlotFilled]}>
          <Ionicons name={lit ? 'star' : 'star-outline'} size={20}
            color={lit ? '#D48A0B' : '#857F95'} accessible={false} aria-hidden />
        </View>;
      })}
    </View> : <View style={styles.longProgress} aria-hidden accessibilityElementsHidden>
      <Ionicons name={filled ? 'star' : 'star-outline'} size={19} color={filled ? '#D48A0B' : '#857F95'} accessible={false} aria-hidden />
      <View style={styles.starTrack}><View style={[styles.starFill, { width: (100 * filled / goal) + '%' }]} /></View>
    </View>}
    <Text style={[styles.starCount, filled === goal && styles.starCountComplete]}>{known ? filled + '/' + goal : goal} sao</Text>
  </View>;
}

export function RankGuide({ onClose, profile }: { onClose: () => void; profile?: StudentProfile }) {
  const [rows, setRows] = useState<RankMilestone[]>();
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const call = new AbortController();
    void profileApi.rankMilestones(call.signal).then(items => {
      if (!call.signal.aborted) setRows(items);
    }).catch(() => { if (!call.signal.aborted) setFailed(true); });
    return () => call.abort();
  }, [retry]);
  return <LessonSheet title="Các bậc xếp hạng" onClose={onClose}>
    <Text style={s.body}>Hoàn thành bài học, Quiz và lượt chơi đủ điều kiện để tích sao và tiến lên các bậc xếp hạng.</Text>
    {failed ? <RecoveryNotice title="Chưa tải được các bậc" message="Em kiểm tra kết nối rồi thử lại nhé."
      actions={[{ label: 'Thử lại', onPress: () => { setFailed(false); setRetry(n => n + 1); } }]} />
      : rows ? <View style={styles.journey}>{rows.map((row, index) => {
        const current = profile?.rank.name === row.name;
        const reached = !!profile && profile.stars >= row.stars && (!row.top || profile.rank.name === row.name);
        const major = row.name.replace(/ [IV]+$/, '');
        const tone = rankTones[rankNames.indexOf(major)] ?? rankTones[0];
        const nextRow = rows[index + 1];
        const cost = nextRow ? nextRow.stars - row.stars : 0;
        const earned = profile ? Math.min(cost, Math.max(0, profile.stars - row.stars)) : undefined;
        return <View key={row.name} testID="rank-milestone" style={styles.step}>
          <View style={styles.track}>
            {index !== rows.length - 1 && <View style={[styles.line, { backgroundColor: tone.accent }]} />}
            <View style={[styles.node, { backgroundColor: tone.accent }]}><Text style={styles.number}>{String(index + 1).padStart(2, '0')}</Text></View>
          </View>
          <LinearGradient colors={[tone.light, '#FFFFFF']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={[styles.level, { borderColor: tone.border }, current && { borderColor: tone.accent, borderWidth: 2 }]}>
            <View style={styles.levelMain}>
              <View style={[styles.iconStage, { backgroundColor: tone.halo }]}><RankEmblem name={row.name} size={72} /></View>
              <View style={styles.copy}><Text style={styles.levelName}>{row.name}</Text>
                <Text style={styles.requirement}>{row.top ? 'Từ ' + row.stars + ' sao và thuộc Top ' + row.top + ' toàn hệ thống' : row.stars === 0 ? 'Khởi đầu · 0 sao' : 'Từ ' + row.stars + ' sao'}</Text>
                {nextRow && cost > 0 ? <Text style={styles.requirement}>{cost} sao để lên {nextRow.name}</Text> : null}
                {nextRow?.top ? <Text style={styles.requirement}>Đạt Top {nextRow.top} để lên {nextRow.name}</Text> : null}
                {current ? <Text style={[styles.status, { color: tone.text }]}>Cấp hiện tại</Text> : reached ? <Text style={[styles.status, { color: tone.text }]}>Đã đạt</Text> : null}
              </View>
              {profile && <View style={styles.endMark}><Ionicons name={current ? 'flag' : reached ? 'checkmark-circle' : 'lock-closed-outline'} size={18} color={tone.text} accessible={false} aria-hidden /></View>}
            </View>
            {cost > 0 ? <RankStarProgress earned={earned} goal={cost} /> : null}
          </LinearGradient>
        </View>;
      })}</View> : <ActivityIndicator accessibilityLabel="Đang tải các bậc xếp hạng" />}
  </LessonSheet>;
}
const tones = (values: string[][]) => values.map(([light, halo, border, accent, text]) => ({ light, halo, border, accent, text }));
const rankNames = ['Sắt', 'Đồng', 'Bạc', 'Vàng', 'Bạch Kim', 'Kim Cương', 'Cao Thủ', 'Đại Cao Thủ', 'Thách Đấu', 'Huyền Thoại'];
const rankTones = tones([
  ['#EAF5FC','#D2E9F8','#B6D4E8','#547B9A','#385975'],
  ['#FFF0E1','#FFE0BB','#EFCDAA','#B87840','#80491D'],
  ['#EDF4FF','#DDEBFF','#C6D9F2','#587EAD','#385C88'],
  ['#FFF7DB','#FFF0B3','#ECD38B','#B78B24','#795817'],
  ['#E9FCFF','#CFF5FF','#B6E4F1','#288CA9','#176078'],
  ['#F3EBFF','#E6D5FF','#D6BEF5','#8050CF','#5B32A2'],
  ['#FAEEFF','#EEDCFF','#E2C1F5','#9D4CC3','#753292'],
  ['#FFF1D8','#FFE4A9','#F1CD80','#B97820','#805111'],
  ['#FFF0EC','#FFDCD4','#F0BDB2','#C95345','#91382C'],
  ['#FFF3D5','#FFE6A6','#EAC77A','#B78019','#805613'],
]);
const styles = StyleSheet.create({
  journey: { gap: 9 },
  step: { flexDirection: 'row', alignItems: 'stretch', gap: 8 },
  track: { width: 26, alignItems: 'center', justifyContent: 'center' },
  line: { position: 'absolute', top: '50%', bottom: -10, width: 2, opacity: .35 },
  node: { width: 25, height: 25, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  number: { fontFamily: FONTS.bold, fontSize: 11, color: '#FFF' },
  level: { flex: 1, minWidth: 0, gap: 8, padding: 10, borderWidth: 1, borderRadius: 17 },
  levelMain: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  starProgress: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 6, minWidth: 0, paddingHorizontal: 8, paddingVertical: 6, borderRadius: 11, backgroundColor: '#FFFFFFB8', borderWidth: 1, borderColor: '#DBD7E5' },
  starSlots: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 4 },
  starSlot: { width: 23, height: 25, alignItems: 'center', justifyContent: 'center', borderRadius: 7 },
  starSlotFilled: { backgroundColor: '#FFF0B8' },
  starCount: { color: '#554C6F', fontFamily: FONTS.bold, fontSize: 12, fontVariant: ['tabular-nums'], flexShrink: 0 },
  starCountComplete: { color: '#815505' },
  longProgress: { flex: 1, minWidth: 60, flexDirection: 'row', alignItems: 'center', gap: 7 },
  starTrack: { flex: 1, height: 7, borderRadius: 5, backgroundColor: '#DED8E8', overflow: 'hidden' },
  starFill: { height: 7, borderRadius: 5, backgroundColor: '#E8A51E' },
  iconStage: { width: 76, height: 76, borderRadius: 38, alignItems: 'center', justifyContent: 'center' },
  levelName: { color: '#25204C', fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 21 },
  requirement: { color: '#534C70', fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 18 },
  status: { fontFamily: FONTS.bold, fontSize: 11, lineHeight: 15 },
  endMark: { width: 18, alignItems: 'center', justifyContent: 'center' },
  copy: { flex: 1, minWidth: 0, gap: 4 },
});
