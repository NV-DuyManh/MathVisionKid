import React, { useEffect, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { COLORS, FONTS } from '../../constants/theme';
import { StudentAvatar } from './ProfileCards';
import { useStudentProfile } from './useStudentProfile';
import { readStudentUsageWeek, type StudentUsageWeek } from './studentUsage';
import { openParentMode, parentControlError, readParentControlStatus, saveParentDailyLimit, type ParentSettings } from './parentControlApi';

type Panel = 'setup' | 'unlock' | 'overview';
const PIN_LENGTH = 6;
export function ParentModePreview({ owner, onExit }: { owner: string; onExit: () => void }) {
  const [ready, setReady] = useState(false);
  const [sessionFailed, setSessionFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  const [busy, setBusy] = useState(false);
  const [settings, setSettings] = useState<ParentSettings>({ dailyMinutes: null });
  const [panel, setPanel] = useState<Panel>('setup');
  const [pin, setPin] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');
  const [section, setSection] = useState<'overview' | 'limits'>('overview');
  const { width } = useWindowDimensions();
  const wide = width >= 760;

  useEffect(() => {
    const request = new AbortController();
    void readParentControlStatus(request.signal).then(status => {
      if (request.signal.aborted) return;
      setReady(true);
      setPanel(status.pinConfigured ? 'unlock' : 'setup');
    }).catch(() => { if (!request.signal.aborted) setSessionFailed(true); });
    return () => request.abort();
  }, [owner, retry]);

  function show(next: Panel) {
    setPin('');
    setConfirmation('');
    setError('');
    setPanel(next);
  }

  async function submit() {
    if (!ready || busy) return;
    if (pin.length !== PIN_LENGTH) {
      setError('Nhập đủ 6 chữ số của mã PIN.');
      return;
    }
    if (panel === 'setup' && pin !== confirmation) {
      setError('Hai mã PIN chưa giống nhau.');
      return;
    }
    setBusy(true);
    try {
      setSettings(await openParentMode(pin, panel === 'setup'));
      show('overview');
    } catch (cause) {
      setError(parentControlError(cause));
      if (panel === 'setup') {
        const status = await readParentControlStatus().catch(() => null);
        if (status?.pinConfigured) setPanel('unlock');
      }
    } finally {
      setBusy(false);
    }
  }

  const setup = panel === 'setup';
  return <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
    <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={[styles.page, wide && styles.pageWide]}>
        <View style={styles.toolbar}>
          <AppButton title="Về hồ sơ" variant="secondary" onPress={onExit}
            icon={<Ionicons name="arrow-back" size={19} color={COLORS.primaryDark} accessible={false} aria-hidden />} />
          {panel === 'overview' && <AppButton title="Khóa" accessibilityLabel="Khóa Góc phụ huynh" variant="ghost" onPress={() => show('unlock')}
            icon={<Ionicons name="lock-closed-outline" size={18} color={COLORS.textSecondary} accessible={false} aria-hidden />} />}
        </View>
        {!ready ? <View style={styles.surface}>
          {sessionFailed ? <>
            <Text accessibilityRole="alert" style={styles.body}>Chưa mở được Góc phụ huynh.</Text>
            <AppButton title="Thử lại" variant="secondary" onPress={() => { setSessionFailed(false); setRetry(value => value + 1); }} />
          </>
            : <ActivityIndicator accessibilityLabel="Đang mở Góc phụ huynh" />}
        </View> : panel === 'overview' ? <>
          <View style={styles.dashboardTitle}>
            <Text accessibilityRole="header" style={styles.title}>Góc phụ huynh</Text>
            <Text style={styles.body}>Theo dõi nhịp học và thiết lập giới hạn cho con.</Text>
          </View>
          <View style={styles.segment}>
            <SectionButton title="Tổng quan" icon="grid-outline" active={section === 'overview'} onPress={() => setSection('overview')} />
            <SectionButton title="Giới hạn" icon="options-outline" active={section === 'limits'} onPress={() => setSection('limits')} />
          </View>
          {section === 'overview' ? <ParentOverview owner={owner} wide={wide} />
            : <DailyUsageLimit minutes={settings.dailyMinutes} onSave={setSettings} />}
        </> : <View style={[styles.gate, wide && styles.gateWide]}>
          <View style={[styles.hero, styles.gateHero, wide && styles.gateColumn]}>
            <View style={styles.heroIcon}><Ionicons name="shield-checkmark-outline" size={31} color={COLORS.surface} accessible={false} aria-hidden /></View>
            <Text accessibilityRole="header" style={styles.heroTitle}>Góc phụ huynh</Text>
            <Text style={styles.heroCopy}>Một nơi để theo dõi tiến độ và quản lý giới hạn học tập của con.</Text>
          </View>
          <View style={[styles.surface, wide && styles.gateColumn]}>
            <View style={styles.intro}>
              <Text accessibilityRole="header" style={styles.heading}>{setup ? 'Thiết lập mã PIN' : 'Nhập mã PIN'}</Text>
              <Text style={styles.body}>{setup ? 'Dành cho phụ huynh. Hãy chọn 6 chữ số và giữ mã này ở nơi an toàn.' : 'Dùng mã 6 chữ số đã thiết lập cho tài khoản của con.'}</Text>
            </View>
            <PinField label="Mã PIN" value={pin} autoFocus={wide} onChange={(next) => { setPin(next); setError(''); }} />
            {setup && <PinField label="Xác nhận mã PIN" value={confirmation} onChange={(next) => { setConfirmation(next); setError(''); }} />}
            {error !== '' && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
            <AppButton title={setup ? 'Lưu mã PIN' : 'Mở Góc phụ huynh'} onPress={() => { void submit(); }} loading={busy} />
          </View>
        </View>}
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}

type IconName = React.ComponentProps<typeof Ionicons>['name'];

function SectionButton({ title, icon, active, onPress }: { title: string; icon: IconName; active: boolean; onPress: () => void }) {
  const color = active ? COLORS.primaryDark : COLORS.textSecondary;
  return <Pressable accessibilityRole="button" accessibilityState={{ selected: active }} aria-pressed={active} onPress={onPress}
    style={({ pressed }) => [styles.segmentButton, active && styles.segmentActive, pressed && styles.pressed]}>
    <Ionicons name={icon} size={18} color={color} accessible={false} aria-hidden />
    <Text style={[styles.segmentText, { color }]}>{title}</Text>
  </Pressable>;
}

function ParentOverview({ owner, wide }: { owner: string; wide: boolean }) {
  const profile = useStudentProfile(owner);
  const usage = useStudentUsageWeek();
  const student = profile.value;
  if (!student) return <View style={styles.surface}>
    {profile.failed ? <>
      <Text accessibilityRole="alert" style={styles.body}>Chưa tải được tổng quan học tập.</Text>
      <AppButton title="Thử lại" variant="secondary" onPress={profile.retry} />
    </> : <ActivityIndicator accessibilityLabel="Đang tải tổng quan học tập" />}
  </View>;
  const { stats } = student;
  return <>
    <View style={styles.hero}>
      <View style={styles.heroIdentity}>
        <StudentAvatar id={student.avatar} size={44} />
        <View style={styles.heroIdentityCopy}>
          <Text style={styles.heroName}>{student.displayName}</Text>
          {student.gradeLevel != null && <Text style={styles.heroCopy}>Lớp {student.gradeLevel}</Text>}
        </View>
      </View>
      <View style={styles.week}>
        <Text style={styles.weekNumber}>{stats.week}</Text>
        <Text style={styles.heroCopy}>hoạt động hoàn thành trong 7 ngày gần đây</Text>
      </View>
    </View>
    <View style={[styles.metrics, wide && styles.metricsWide]}>
      <Metric wide={wide} art={require('../../../assets/illustrations/approved/practice.webp')} tint={COLORS.pastelBlue} label="Hoạt động hôm nay" value={String(stats.today)} />
      <Metric wide={wide} art={require('../../../assets/illustrations/web/streak-flame.webp')} tint={COLORS.pastelAmber} label="Chuỗi học hiện tại" value={`${stats.streak} ngày`} />
      <Metric wide={wide} art={require('../../../assets/illustrations/web/progress-bars.webp')} tint={COLORS.primaryLight} label="Tổng số ngày học" value={String(stats.days)} />
      <Metric wide={wide} icon="time" tint={COLORS.pastelGreen} color="#176A50" label="Thời gian tuần này" value={usage.week ? formatUsage(usage.week.totalMillis) : '—'} />
    </View>
    <StudentUsageChart {...usage} />
    <View style={styles.surface}>
      <Text accessibilityRole="header" style={styles.heading}>Hoạt động đã hoàn thành</Text>
      <Text style={styles.body}>Tính từ khi bắt đầu sử dụng tài khoản.</Text>
      <ActivityRow icon="book-outline" label="Bài học" value={stats.lessons} />
      <ActivityRow icon="list-outline" label="Quiz" value={stats.quizzes} />
      <ActivityRow icon="game-controller-outline" label="Game" value={stats.games} />
    </View>
  </>;
}

const WEEKDAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

function useStudentUsageWeek() {
  const [week, setWeek] = useState<StudentUsageWeek>();
  const [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const request = new AbortController();
    let fetching = false;
    const refresh = () => {
      if (fetching || request.signal.aborted) return;
      fetching = true;
      void readStudentUsageWeek(request.signal).then(data => {
        if (!request.signal.aborted) { setWeek(data); setFailed(false); }
      }).catch(() => { if (!request.signal.aborted) setFailed(true); }).finally(() => { fetching = false; });
    };
    refresh();
    const interval = setInterval(refresh, 10_000);
    return () => { request.abort(); clearInterval(interval); };
  }, [revision]);
  return { week, failed, retry: () => { setFailed(false); setRevision(value => value + 1); } };
}

function formatUsage(milliseconds: number) {
  const minutes = Math.floor(milliseconds / 60_000);
  if (milliseconds > 0 && minutes === 0) return '< 1 phút';
  return minutes < 60 ? `${minutes} phút` : `${Math.floor(minutes / 60)} giờ ${minutes % 60} phút`;
}

function StudentUsageChart({ week, failed, retry }: ReturnType<typeof useStudentUsageWeek>) {
  const max = Math.max(1, ...(week?.days.map(day => day.elapsedMillis) ?? []));
  return <View style={styles.surface}>
    <View style={styles.intro}>
      <Text accessibilityRole="header" style={styles.heading}>Thời gian dùng app theo ngày</Text>
      <Text style={styles.body}>Tính thời gian từ khi mở Student App hoặc Student Web trong phiên đăng nhập.</Text>
    </View>
    {failed ? <>
      <Text accessibilityRole="alert" style={styles.error}>Chưa tải được thời gian sử dụng.</Text>
      <AppButton title="Tải lại thời gian" variant="secondary" onPress={retry} />
    </> : !week ? <ActivityIndicator accessibilityLabel="Đang tải thời gian sử dụng" /> : <>
      <View style={styles.chart}>
        {week.days.map((day, index) => {
          const future = day.date > week.today;
          const today = day.date === week.today;
          const minutes = Math.floor(day.elapsedMillis / 60000);
          const label = day.elapsedMillis > 0 && minutes === 0 ? '<1p'
            : minutes >= 60 ? `${Math.floor(minutes / 60)}g${minutes % 60 || ''}` : `${minutes}p`;
          const description = future ? 'Sắp tới' : formatUsage(day.elapsedMillis);
          return <View key={day.date} accessible accessibilityLabel={`${WEEKDAYS[index]}, ${description}`} style={[styles.chartDay, today && styles.chartToday]}>
            <Text style={styles.chartValue}>{future ? '—' : label}</Text>
            <View style={styles.chartTrack}>
              {day.elapsedMillis > 0 && <View style={[styles.chartBar, { height: Math.max(4, 52 * day.elapsedMillis / max) }]} />}
            </View>
            <Text style={[styles.chartLabel, today && styles.chartLabelToday]}>{WEEKDAYS[index]}</Text>
          </View>;
        })}
      </View>
    </>}
  </View>;
}

function Metric({ tint, label, value, wide, ...visual }: { tint: string; label: string; value: string; wide: boolean } &
  ({ art: number } | { icon: IconName; color: string })) {
  return <View style={[styles.metric, wide && styles.metricWide]}>
    <View style={[styles.metricIcon, { backgroundColor: tint }]}>
      {'art' in visual ? <AppIllustration source={visual.art} style={styles.metricArt} accessible={false} />
        : <Ionicons name={visual.icon} color={visual.color} size={23} accessible={false} aria-hidden />}
    </View>
    <View style={styles.metricCopy}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  </View>;
}

function ActivityRow({ icon, label, value }: { icon: IconName; label: string; value: number }) {
  return <View style={styles.activityRow}>
    <Ionicons name={icon} size={20} color={COLORS.primaryDark} accessible={false} aria-hidden />
    <Text style={styles.activityLabel}>{label}</Text>
    <Text style={styles.section}>{value}</Text>
  </View>;
}

function DailyUsageLimit({ minutes, onSave }: { minutes: number | null; onSave: (value: ParentSettings) => void }) {
  const [value, setValue] = useState(minutes?.toString() ?? '');
  const [pin, setPin] = useState('');
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  async function save() {
    const next = value === '' ? null : Number(value);
    setSaved(false);
    setError('');
    if (next !== null && (next < 1 || next > 1440)) {
      setError('Nhập từ 1 đến 1.440 phút hoặc để trống.');
      return;
    }
    if (pin.length !== PIN_LENGTH) {
      setError('Nhập mã PIN để lưu giới hạn.');
      return;
    }
    setBusy(true);
    try {
      const settings = await saveParentDailyLimit(pin, next);
      onSave(settings);
      setValue(settings.dailyMinutes?.toString() ?? '');
      setSaved(true);
    } catch (cause) {
      setError(parentControlError(cause));
    } finally {
      setPin('');
      setBusy(false);
    }
  }

  return <View style={styles.surface}>
    <View style={styles.settingHeader}>
      <View style={[styles.settingIcon, { backgroundColor: COLORS.pastelGreen }]}>
        <Ionicons name="hourglass-outline" size={23} color={COLORS.primaryDark} accessible={false} aria-hidden />
      </View>
      <View style={styles.settingCopy}>
        <Text accessibilityRole="header" style={styles.heading}>Tổng thời gian mỗi ngày</Text>
        <Text style={styles.body}>Tính chung thời gian trên web và app. Khi hết giờ, con sẽ thấy màn hình nghỉ. Để trống nếu muốn dùng không giới hạn.</Text>
      </View>
    </View>
    <TextInput accessibilityLabel="Số phút dùng app mỗi ngày" inputMode="numeric" maxLength={4}
      placeholder="Không giới hạn" placeholderTextColor={COLORS.textMuted} style={styles.input} value={value}
      editable={!busy} onChangeText={text => { setValue(text.replace(/[^0-9]/g, '')); setError(''); setSaved(false); }} />
    <PinField label="Mã PIN để lưu" value={pin} onChange={setPin} />
    {error !== '' && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
    {saved && <Text accessibilityLiveRegion="polite" style={styles.body}>Đã lưu giới hạn trên tài khoản.</Text>}
    <AppButton title="Lưu giới hạn" onPress={() => { void save(); }} loading={busy} />
  </View>;
}

function PinField({ label, value, onChange, autoFocus = false }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  autoFocus?: boolean;
}) {
  return <View style={styles.field}>
    <Text style={styles.section}>{label}</Text>
    <TextInput
      accessibilityLabel={label}
      autoComplete="off"
      autoFocus={autoFocus}
      inputMode="numeric"
      maxLength={PIN_LENGTH}
      onChangeText={(text) => onChange(text.replace(/[^0-9]/g, ''))}
      secureTextEntry
      style={styles.input}
      value={value}
    />
  </View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  page: { width: '100%', maxWidth: 1056, alignSelf: 'center', paddingHorizontal: 16, paddingTop: 14, paddingBottom: 36, gap: 18 },
  pageWide: { paddingHorizontal: 32, paddingTop: 26, gap: 22 },
  toolbar: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  dashboardTitle: { gap: 2 },
  title: { fontFamily: FONTS.black, fontSize: 32, letterSpacing: -.7, color: COLORS.textPrimary },
  gate: { gap: 14 },
  gateWide: { flexDirection: 'row', alignItems: 'stretch', gap: 16 },
  hero: { backgroundColor: COLORS.primaryDark, padding: 24, borderRadius: 24, gap: 20 },
  gateHero: { paddingVertical: 28, justifyContent: 'center', gap: 12 },
  gateColumn: { flex: 1, justifyContent: 'center' },
  heroIcon: { alignSelf: 'flex-start', padding: 12, backgroundColor: '#FFFFFF24', borderRadius: 16, marginBottom: 4 },
  heroTitle: { fontFamily: FONTS.black, fontSize: 30, lineHeight: 36, color: COLORS.surface, letterSpacing: -.6 },
  heroCopy: { color: COLORS.primaryLight, fontFamily: FONTS.semiBold, fontSize: 15, lineHeight: 21, flexShrink: 1 },
  heroIdentity: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  heroIdentityCopy: { flex: 1, minWidth: 0 },
  heroName: { fontFamily: FONTS.extraBold, color: COLORS.surface, fontSize: 20 },
  week: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingTop: 14, borderTopWidth: 1, borderTopColor: '#FFFFFF48' },
  weekNumber: { fontFamily: FONTS.black, fontSize: 42, lineHeight: 48, color: COLORS.surface },
  surface: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 22, gap: 16, padding: 20 },
  segment: { flexDirection: 'row', gap: 4, padding: 4, borderRadius: 16, backgroundColor: COLORS.surfaceSubdued, borderWidth: 1, borderColor: COLORS.border },
  segmentButton: { flex: 1, minHeight: 48, borderRadius: 12, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 7, paddingHorizontal: 5 },
  segmentActive: { backgroundColor: COLORS.surface },
  segmentText: { fontFamily: FONTS.extraBold, fontSize: 15 },
  pressed: { opacity: .72 },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  metricsWide: { flexWrap: 'nowrap', gap: 12 },
  metric: { flexGrow: 1, flexBasis: '45%', minWidth: 0, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 18, padding: 11, flexDirection: 'row', alignItems: 'center', gap: 8 },
  metricWide: { flexBasis: 0 },
  metricIcon: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', borderRadius: 13 },
  metricArt: { width: 38, height: 38 },
  metricCopy: { flex: 1, minWidth: 0, gap: 2 },
  metricValue: { fontFamily: FONTS.black, fontSize: 19, lineHeight: 25, color: COLORS.textPrimary },
  metricLabel: { fontFamily: FONTS.semiBold, fontSize: 13, color: COLORS.textSecondary },
  activityRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 8, borderTopWidth: 1, borderTopColor: COLORS.border },
  activityLabel: { flex: 1, fontFamily: FONTS.bold, fontSize: 15, color: COLORS.textPrimary },
  chart: { flexDirection: 'row', gap: 4, alignItems: 'stretch' },
  chartDay: { flex: 1, minWidth: 0, borderRadius: 10, paddingVertical: 7, alignItems: 'center', gap: 4 },
  chartToday: { backgroundColor: COLORS.surfaceSubdued },
  chartTrack: { height: 53, width: '58%', borderBottomWidth: 1, borderBottomColor: COLORS.border, justifyContent: 'flex-end' },
  chartBar: { backgroundColor: COLORS.primaryDark, borderTopLeftRadius: 4, borderTopRightRadius: 4 },
  chartValue: { fontFamily: FONTS.semiBold, fontSize: 12, color: COLORS.textSecondary },
  chartLabel: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.textSecondary },
  chartLabelToday: { color: COLORS.primaryDark },
  settingHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  settingIcon: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 12 },
  settingCopy: { flex: 1, minWidth: 0, gap: 3 },
  intro: { gap: 6 },
  heading: { fontFamily: FONTS.bold, fontSize: 21, color: COLORS.textPrimary },
  section: { fontFamily: FONTS.bold, fontSize: 16, color: COLORS.textPrimary },
  body: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 22, color: COLORS.textSecondary },
  field: { gap: 7 },
  input: { minHeight: 48, borderWidth: 1, borderColor: COLORS.textMuted, borderRadius: 12, paddingHorizontal: 12, backgroundColor: COLORS.surface, color: COLORS.textPrimary, fontFamily: FONTS.bold, fontSize: 19 },
  error: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.error },
});
