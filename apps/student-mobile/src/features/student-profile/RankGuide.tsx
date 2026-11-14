import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { LessonSheet } from '../tutoring/LessonSheet';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { profileApi, type RankMilestone } from './profileApi';
import { RankEmblem } from './RankEmblem';
import { profileStyles as s } from './ProfileCards';

export function RankGuide({ onClose }: { onClose: () => void }) {
  const [rows, setRows] = useState<RankMilestone[]>();
  const [failed, setFailed] = useState(false);
  const [tryCount, setTryCount] = useState(0);
  useEffect(() => {
    const call = new AbortController();
    void profileApi.rankMilestones(call.signal).then(items => {
      if (!call.signal.aborted) setRows(items);
    }).catch(() => {
      if (!call.signal.aborted) setFailed(true);
    });
    return () => call.abort();
  }, [tryCount]);
  return <LessonSheet title="Các bậc xếp hạng" onClose={onClose}>
    <Text style={s.body}>Em tích sao khi hoàn thành bài học, Quiz hoặc thử thách tính sao đủ điều kiện.</Text>
    {failed ? <RecoveryNotice title="Chưa tải được các bậc" message="Em kiểm tra kết nối rồi thử lại nhé."
      actions={[{ label: 'Thử lại', onPress: () => { setFailed(false); setTryCount(count => count + 1); } }]} />
      : rows ? rows.map(row => <View key={row.name} style={s.row}>
        <RankEmblem name={row.name} size={42} />
        <View style={{ flex: 1, minWidth: 110 }}>
          <Text style={s.heading}>{row.name}</Text>
          <Text style={s.body}>{row.top ? `Từ ${row.stars} sao và thuộc Top ${row.top} toàn hệ thống` : `Từ ${row.stars} sao`}</Text>
        </View>
      </View>) : <ActivityIndicator accessibilityLabel="Đang tải các bậc xếp hạng" />}
  </LessonSheet>;
}
