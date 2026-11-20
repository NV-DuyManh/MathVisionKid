import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { AppButton } from '../../components/ui/AppButton';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { COLORS, FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { StudentAvatar } from './ProfileCards';
import type { StudentProfile } from './profileApi';
import { readStudentUsageWeek, type StudentUsageWeek } from './studentUsage';
import { useStudentProfile } from './useStudentProfile';

const WEEKDAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'] as const;
const VIETNAM_DAY = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Ho_Chi_Minh',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});
const SHORT_WEEKDAY = new Intl.DateTimeFormat('vi-VN', { weekday: 'short', timeZone: 'UTC' });
const HISTORY_DATE = new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', timeZone: 'Asia/Ho_Chi_Minh' });

const ILLUSTRATION_PRACTICE = require('../../../assets/illustrations/approved/practice.webp');
const ILLUSTRATION_STREAK = require('../../../assets/illustrations/web/streak-flame.webp');
const ILLUSTRATION_BARS = require('../../../assets/illustrations/web/progress-bars.webp');
const ILLUSTRATION_PROGRESS = require('../../../assets/illustrations/approved/progress.webp');

export function formatDailyLimit(minutes: number | null) {
  return minutes === null ? 'Không giới hạn' : `${minutes} phút/ngày`;
}

export function formatUsage(milliseconds: number) {
  if (milliseconds <= 0) return '0 phút';
  const minutes = Math.floor(milliseconds / 60_000);
  if (minutes === 0) return '< 1 phút';
  if (minutes < 60) return `${minutes} phút`;
  const remainder = minutes % 60;
  return `${Math.floor(minutes / 60)} giờ${remainder ? ` ${remainder} phút` : ''}`;
}

function formatChartDayValue(milliseconds: number) {
  if (milliseconds <= 0) return '0 phút';
  const minutes = Math.floor(milliseconds / 60_000);
  if (minutes === 0) return '<1p';
  if (minutes < 60) return `${minutes}p`;
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder ? `${hours}g${remainder}p` : `${hours} giờ`;
}

export function useUsageWeek() {
  const [week, setWeek] = useState<StudentUsageWeek>();
  const [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const request = new AbortController();
    let fetching = false;
    const refresh = () => {
      if (fetching || request.signal.aborted) return;
      fetching = true;
      void readStudentUsageWeek(request.signal)
        .then(data => {
          if (!request.signal.aborted) {
            setWeek(data);
            setFailed(false);
          }
        })
        .catch(() => {
          if (!request.signal.aborted) {
            setFailed(true);
            setWeek(undefined);
          }
        })
        .finally(() => {
          fetching = false;
        });
    };
    refresh();
    const interval = setInterval(refresh, 10_000);
    return () => {
      request.abort();
      clearInterval(interval);
    };
  }, [revision]);
  return {
    week,
    failed,
    retry: () => {
      setFailed(false);
      setRevision(value => value + 1);
    },
  };
}

export function ParentHeroBanner({
  student,
  dailyMinutes,
  limitUncertain,
  onEditLimit,
}: {
  student?: StudentProfile;
  dailyMinutes: number | null;
  limitUncertain: boolean;
  onEditLimit?: () => void;
}) {
  const { width } = useWindowDimensions();
  const wide = width >= 760;
  const unlockedTitles = student?.titles.filter(title => title.unlocked).length ?? 0;

  return (
    <LinearGradient
      colors={['#FCFAFF', '#EDE3FD', '#DDD0FA']}
      start={{ x: 0, y: 0.2 }}
      end={{ x: 1, y: 0.9 }}
      style={[styles.heroBanner, wide && styles.heroBannerWide]}
    >
      <View style={styles.heroIdentityRow}>
        <View style={styles.heroAvatarWrap}>
          <StudentAvatar id={student?.avatar ?? 'star'} photo={student?.avatarPhoto} size={wide ? 58 : 48} />
        </View>
        <View style={styles.identityCopy}>
          <View style={styles.heroBadgeRow}>
            <View style={styles.heroRolePill}>
              <Ionicons name="shield-checkmark" size={14} color={STUDENT_WEB.primary} accessible={false} aria-hidden />
              <Text style={styles.heroRoleText}>Góc phụ huynh</Text>
            </View>
            {student && (
              <View style={styles.heroStarPill}>
                <Ionicons name="star" size={13} color="#956300" accessible={false} aria-hidden />
                <Text style={styles.heroStarText}>{student.stars} sao · {student.rank.name}</Text>
              </View>
            )}
          </View>
          <Text style={[styles.heroName, !wide && styles.heroNameCompact]} numberOfLines={1}>
            {student?.displayName ?? 'Học sinh MathVision'}
          </Text>
          <Text style={styles.heroMeta}>
            {student?.gradeLevel !== null && student?.gradeLevel !== undefined ? `Lớp ${student.gradeLevel}` : 'Tài khoản học sinh'}
            {student?.classrooms?.length ? ` · ${student.classrooms.map(c => c.name).join(', ')}` : ''}
            {unlockedTitles > 0 ? ` · ${unlockedTitles} danh hiệu` : ''}
          </Text>
        </View>
      </View>

      <View style={[styles.heroQuickPills, wide && styles.heroQuickPillsWide]}>
        {student && (
          <View style={styles.heroStatPill}>
            <Text style={styles.heroStatLabel}>7 ngày gần đây</Text>
            <Text style={styles.heroStatValue}>{student.stats.week} hoạt động</Text>
          </View>
        )}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Giới hạn: ${formatDailyLimit(dailyMinutes)}. Nhấn để chỉnh sửa`}
          onPress={onEditLimit}
          style={({ pressed }) => [styles.heroStatPill, styles.heroLimitPill, pressed && styles.pressed]}
        >
          <Text style={styles.heroStatLabel}>{limitUncertain ? 'Xác nhận gần nhất' : 'Giới hạn mỗi ngày'}</Text>
          <View style={styles.heroLimitValueRow}>
            <Text style={[styles.heroStatValue, styles.heroLimitValue]}>{formatDailyLimit(dailyMinutes)}</Text>
            <Ionicons name="chevron-forward" size={15} color={STUDENT_WEB.primary} accessible={false} aria-hidden />
          </View>
        </Pressable>
      </View>
    </LinearGradient>
  );
}

export function ParentOverview({
  owner,
  dailyMinutes,
  limitUncertain,
  onEditLimit,
}: {
  owner: string;
  dailyMinutes: number | null;
  limitUncertain: boolean;
  onEditLimit: () => void;
}) {
  const profile = useStudentProfile(owner);
  const usage = useUsageWeek();
  const student = profile.failed ? undefined : profile.value;
  const { width } = useWindowDimensions();
  const desktop = width >= 900;
  const twoColumns = width >= 350;
  const compact = width < 600;

  return (
    <View style={styles.overviewRoot}>
      <ParentHeroBanner
        student={student}
        dailyMinutes={dailyMinutes}
        limitUncertain={limitUncertain}
        onEditLimit={onEditLimit}
      />

      {student && (
        <OverviewMetrics
          stats={student.stats}
          week={usage.week}
          failed={usage.failed}
          desktop={desktop}
          twoColumns={twoColumns}
        />
      )}

      <View style={[styles.columns, desktop && styles.columnsWide]}>
        <View style={[styles.panel, desktop && styles.primaryChartColumn]}>
          <PanelHeading
            title="Sử dụng an toàn"
            subtitle="Thời gian mở app từ thứ Hai đến Chủ nhật (đơn vị: phút)"
            icon="shield-checkmark-outline"
            safe
            badge="Tuần hiện tại"
          />
          <UsageSummary
            {...usage}
            dailyMinutes={dailyMinutes}
            limitUncertain={limitUncertain}
            onEditLimit={onEditLimit}
            compact={compact}
          />
        </View>

        <View style={[styles.panel, desktop && styles.secondaryChartColumn]}>
          <PanelHeading
            title="Tiến độ học tập"
            subtitle="Phân bổ theo từng dạng hoạt động đã xác minh"
            icon="book-outline"
          />
          {student ? (
            <LearningProgress stats={student.stats} history={student.history} />
          ) : profile.failed ? (
            <LoadError message="Chưa tải được tiến độ học tập." action="Tải lại tiến độ" onRetry={profile.retry} />
          ) : (
            <View style={styles.loadingBox}>
              <ActivityIndicator color={COLORS.primary} accessibilityLabel="Đang tải tiến độ học tập" />
              <Text style={styles.body}>Đang tải tiến độ học tập…</Text>
            </View>
          )}
          <View style={styles.guide}>
            <View style={styles.guideIcon}>
              <Ionicons name="chatbubble-ellipses-outline" size={19} color="#92400E" accessible={false} aria-hidden />
            </View>
            <View style={styles.guideCopy}>
              <Text style={styles.guideTitle}>Gợi ý đồng hành</Text>
              <Text style={styles.body}>“Con muốn kể bố mẹ nghe bài toán nào?”</Text>
            </View>
          </View>
        </View>
      </View>

      {student && (
        <View style={[styles.columns, desktop && styles.columnsWide]}>
          <View style={[styles.panel, desktop && styles.equalColumn]}>
            <PanelHeading
              title="Hoạt động gần đây"
              subtitle="Những lần hoàn thành có ghi nhận sao gần nhất"
              icon="sparkles-outline"
            />
            <RecentActivityFeed history={student.history} />
          </View>

          <View style={[styles.panel, desktop && styles.equalColumn]}>
            <PanelHeading
              title="Tổng hợp học tập"
              subtitle="Số liệu tích lũy từ khi bắt đầu tài khoản"
              icon="bar-chart-outline"
            />
            <View style={styles.summaryTiles}>
              <View style={styles.summaryTile}>
                <Text style={styles.summaryTileLabel}>Bài học hoàn thành</Text>
                <Text style={styles.summaryTileValue}>{student.stats.lessons}</Text>
              </View>
              <View style={styles.summaryTile}>
                <Text style={styles.summaryTileLabel}>Quiz giải đúng</Text>
                <Text style={styles.summaryTileValue}>{student.stats.quizzes}</Text>
              </View>
              <View style={styles.summaryTile}>
                <Text style={styles.summaryTileLabel}>Lượt chơi đạt yêu cầu</Text>
                <Text style={styles.summaryTileValue}>{student.stats.games}</Text>
              </View>
              <View style={styles.summaryTile}>
                <Text style={styles.summaryTileLabel}>Hoạt động 30 ngày</Text>
                <Text style={styles.summaryTileValue}>{student.stats.month}</Text>
              </View>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

function OverviewMetrics({
  stats,
  week,
  failed,
  desktop,
  twoColumns,
}: {
  stats: StudentProfile['stats'];
  week?: StudentUsageWeek;
  failed: boolean;
  desktop: boolean;
  twoColumns: boolean;
}) {
  const metrics = [
    {
      label: 'Hoạt động hôm nay',
      value: String(stats.today),
      sub: 'bài hoàn thành',
      art: ILLUSTRATION_PRACTICE,
      cardTint: COLORS.pastelBlue,
      borderTint: '#BFDBFE',
    },
    {
      label: 'Chuỗi học hiện tại',
      value: `${stats.streak} ngày`,
      sub: 'học liên tiếp',
      art: ILLUSTRATION_STREAK,
      cardTint: COLORS.pastelAmber,
      borderTint: '#FDE68A',
    },
    {
      label: 'Ngày có hoạt động',
      value: String(stats.days),
      sub: `${stats.month} lượt / 30 ngày`,
      art: ILLUSTRATION_BARS,
      cardTint: COLORS.pastelPurple,
      borderTint: '#E9D5FF',
    },
    {
      label: 'Thời gian tuần này',
      value: week ? formatUsage(week.totalMillis) : failed ? 'Chưa tải được' : 'Đang tải…',
      sub: 'Thứ 2 – Chủ nhật',
      art: ILLUSTRATION_PROGRESS,
      cardTint: COLORS.pastelGreen,
      borderTint: '#BBF7D0',
    },
  ];

  return (
    <View style={[styles.metrics, desktop && styles.metricsDesktop]}>
      {metrics.map(metric => (
        <View
          key={metric.label}
          style={[
            styles.metric,
            twoColumns ? styles.metricTwoCol : styles.metricOneCol,
            desktop && styles.metricDesktop,
            { backgroundColor: metric.cardTint, borderColor: metric.borderTint },
          ]}
        >
          <View style={[styles.metricIcon, { borderColor: metric.borderTint }]}>
            <AppIllustration source={metric.art} style={styles.metricArt} accessible={false} />
          </View>
          <View style={styles.metricCopy}>
            <Text style={styles.metricLabel}>{metric.label}</Text>
            <Text style={styles.metricValue}>
              {metric.value}
            </Text>
            <Text style={styles.metricSub}>
              {metric.sub}
            </Text>
          </View>
        </View>
      ))}
    </View>
  );
}

function PanelHeading({
  title,
  subtitle,
  icon,
  safe,
  badge,
}: {
  title: string;
  subtitle?: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  safe?: boolean;
  badge?: string;
}) {
  return (
    <View style={styles.panelHeader}>
      <View style={[styles.iconWell, safe && styles.safeIcon]}>
        <Ionicons name={icon} size={22} color={safe ? '#146448' : STUDENT_WEB.primary} accessible={false} aria-hidden />
      </View>
      <View style={styles.identityCopy}>
        <Text accessibilityRole="header" aria-level={2} style={styles.heading}>
          {title}
        </Text>
        {subtitle && <Text style={styles.panelSubtitle}>{subtitle}</Text>}
      </View>
      {badge && (
        <View style={styles.panelBadge}>
          <Text style={styles.panelBadgeText}>{badge}</Text>
        </View>
      )}
    </View>
  );
}

function LearningProgress({
  stats,
  history,
}: {
  stats: StudentProfile['stats'];
  history: StudentProfile['history'];
}) {
  const total = stats.lessons + stats.quizzes + stats.games;
  if (total === 0) {
    return (
      <View style={styles.empty}>
        <Ionicons name="sparkles-outline" size={24} color={STUDENT_WEB.primary} accessible={false} aria-hidden />
        <Text style={styles.label}>Chưa có hoạt động học tập</Text>
        <Text style={styles.body}>Hoàn thành bài học hoặc quiz để xem tiến độ tại đây.</Text>
      </View>
    );
  }

  const distribution = [
    { label: 'Bài học hoàn thành', count: stats.lessons, color: '#7055F6', tint: '#EDE9FF' },
    { label: 'Quiz giải đúng', count: stats.quizzes, color: '#10B981', tint: '#DCFCE7' },
    { label: 'Lượt chơi được ghi nhận', count: stats.games, color: '#F59E0B', tint: '#FEF3C7' },
  ];

  const recent7 = recentHistoryDays(history, new Date());
  const maxRecent = Math.max(1, ...recent7.map(d => d.count));

  return (
    <View style={styles.progressBody}>
      <View style={styles.group}>
        <Text accessibilityRole="header" aria-level={3} style={styles.sectionLabel}>
          Tỉ lệ hoạt động đã hoàn thành ({total} lượt)
        </Text>
        <View style={styles.distList}>
          {distribution.map(item => {
            const pct = Math.round((item.count / total) * 100);
            return (
              <View key={item.label} style={styles.distItem}>
                <View style={styles.distTop}>
                  <Text style={styles.distLabel}>{item.label}</Text>
                  <Text style={styles.distCount}>
                    {item.count} ({pct}%)
                  </Text>
                </View>
                <View style={[styles.distTrack, { backgroundColor: item.tint }]}>
                  <View
                    style={[
                      styles.distFill,
                      {
                        backgroundColor: item.color,
                        width: item.count > 0 ? `${Math.max(4, pct)}%` : '0%',
                      },
                    ]}
                  />
                </View>
              </View>
            );
          })}
        </View>
      </View>

      <View style={styles.group}>
        <Text accessibilityRole="header" aria-level={3} style={styles.sectionLabel}>
          Nhịp nhận sao 7 ngày qua
        </Text>
        {recent7.every(d => d.count === 0) ? (
          <Text style={styles.body}>Chưa có hoạt động mới trong 7 ngày này.</Text>
        ) : (
          <View style={styles.miniChart}>
            {recent7.map(day => (
              <View
                key={day.key}
                accessible
                accessibilityLabel={`${day.label}: ${day.count} hoạt động`}
                style={styles.miniCol}
              >
                <Text style={styles.miniCount}>{day.count}</Text>
                <View style={styles.miniTrack}>
                  <View
                    style={[
                      styles.miniBar,
                      {
                        height: day.count > 0 ? Math.max(8, Math.round((44 * day.count) / maxRecent)) : 3,
                        backgroundColor: day.count > 0 ? '#713CF7' : '#CBD5E1',
                      },
                    ]}
                  />
                </View>
                <Text style={styles.miniLabel}>{day.label}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </View>
  );
}

function recentHistoryDays(history: StudentProfile['history'], now: Date) {
  const date = new Date(`${VIETNAM_DAY.format(now)}T00:00:00Z`);
  const counts = new Map<string, number>();
  for (const row of history) {
    const completedAt = new Date(row.completedAt);
    if (Number.isFinite(completedAt.getTime()) && completedAt <= now) {
      const day = VIETNAM_DAY.format(completedAt);
      counts.set(day, (counts.get(day) ?? 0) + 1);
    }
  }
  return Array.from({ length: 7 }, (_, index) => {
    const day = new Date(date);
    day.setUTCDate(day.getUTCDate() - (6 - index));
    const key = day.toISOString().slice(0, 10);
    return {
      key,
      count: counts.get(key) ?? 0,
      label: index === 6 ? 'Nay' : SHORT_WEEKDAY.format(day),
    };
  });
}

function RecentActivityFeed({ history }: { history: StudentProfile['history'] }) {
  if (!history.length) {
    return (
      <View style={styles.empty}>
        <Text style={styles.label}>Chưa có nhật ký hoạt động</Text>
        <Text style={styles.body}>Khi con hoàn thành bài học, quiz hoặc trò chơi, lịch sử sẽ hiện tại đây.</Text>
      </View>
    );
  }
  const sourceInfo = {
    LESSON: { label: 'Bài học', icon: 'book-outline' as const, tint: COLORS.pastelBlue, color: '#1D4ED8' },
    QUIZ: { label: 'Quiz', icon: 'checkmark-circle-outline' as const, tint: COLORS.pastelGreen, color: '#15803D' },
    GAME: { label: 'Trò chơi', icon: 'game-controller-outline' as const, tint: COLORS.pastelAmber, color: '#B45309' },
  };
  return (
    <View style={styles.feedList}>
      {history.slice(0, 4).map((item, idx) => {
        const meta = sourceInfo[item.source];
        const date = new Date(item.completedAt);
        const dateText = Number.isFinite(date.getTime()) ? HISTORY_DATE.format(date) : '';
        return (
          <View key={`${item.completedAt}-${item.source}-${idx}`} style={styles.feedRow}>
            <View style={[styles.feedIcon, { backgroundColor: meta.tint }]}>
              <Ionicons name={meta.icon} size={18} color={meta.color} accessible={false} aria-hidden />
            </View>
            <View style={styles.identityCopy}>
              <Text style={styles.feedTitle}>{meta.label}</Text>
              <Text style={styles.feedDate}>{dateText}</Text>
            </View>
            <View style={styles.feedStarBadge}>
              <Ionicons name="star" size={13} color="#956300" accessible={false} aria-hidden />
              <Text style={styles.feedStarText}>+{item.stars}</Text>
            </View>
          </View>
        );
      })}
    </View>
  );
}

function LoadError({ message, action, onRetry }: { message: string; action: string; onRetry: () => void }) {
  return (
    <View style={styles.errorCard}>
      <Text accessibilityRole="alert" style={styles.errorTitle}>
        {message}
      </Text>
      <Text style={styles.body}>Kiểm tra kết nối rồi thử lại.</Text>
      <AppButton title={action} variant="secondary" onPress={onRetry} />
    </View>
  );
}

function UsageSummary({
  week,
  failed,
  retry,
  dailyMinutes,
  limitUncertain,
  onEditLimit,
  compact,
}: ReturnType<typeof useUsageWeek> & {
  dailyMinutes: number | null;
  limitUncertain: boolean;
  onEditLimit: () => void;
  compact: boolean;
}) {
  const today = week?.days.find(day => day.date === week.today);
  const todayMinutes = today ? Math.floor(today.elapsedMillis / 60_000) : 0;
  const limitProgress = dailyMinutes ? Math.min(100, Math.round((todayMinutes / dailyMinutes) * 100)) : 0;

  return (
    <View style={styles.usageWrap}>
      <View style={styles.weeklyHighlightCard}>
        <View style={styles.weeklyHighlightMain}>
          <Text style={styles.weeklyHighlightLabel}>TỔNG THỜI GIAN TUẦN NÀY</Text>
          <Text style={styles.weeklyHighlightValue}>
            {week ? formatUsage(week.totalMillis) : failed ? 'Chưa tải được' : 'Đang tải…'}
          </Text>
        </View>
        <View style={styles.weeklyHighlightToday}>
          <Text style={styles.weeklyHighlightTodayLabel}>Hôm nay</Text>
          <Text style={styles.weeklyHighlightTodayValue}>
            {today ? formatUsage(today.elapsedMillis) : failed || week ? '—' : 'Đang tải…'}
          </Text>
        </View>
      </View>

      <View style={styles.safeFacts}>
        <View style={styles.fact}>
          <Text style={styles.factLabel}>{limitUncertain ? 'Giới hạn xác nhận gần nhất' : 'Giới hạn đang áp dụng'}</Text>
          <Text style={styles.factValue}>{formatDailyLimit(dailyMinutes)}</Text>
          {dailyMinutes !== null && today && !limitUncertain && (
            <View style={styles.limitProgressWrap}>
              <View style={styles.limitProgressTrack}>
                <View
                  style={[
                    styles.limitProgressFill,
                    {
                      width: `${Math.max(today.elapsedMillis > 0 ? 4 : 0, limitProgress)}%`,
                      backgroundColor: limitProgress >= 100 ? COLORS.error : '#15803D',
                    },
                  ]}
                />
              </View>
              <Text style={styles.limitProgressText}>
                Đã dùng {todayMinutes}/{dailyMinutes} phút hôm nay ({limitProgress}%)
              </Text>
            </View>
          )}
        </View>
        <AppButton
          title="Đổi giới hạn"
          variant="secondary"
          onPress={onEditLimit}
          style={styles.editLimitBtn}
          icon={<Ionicons name="options-outline" size={17} color={COLORS.primaryDark} accessible={false} aria-hidden />}
        />
      </View>

      <View style={styles.group}>
        <View style={styles.chartSubHeader}>
          <Text accessibilityRole="header" aria-level={3} style={styles.sectionLabel}>
            Biểu đồ thời gian theo ngày (T2 – CN)
          </Text>
        </View>
        {failed ? (
          <LoadError message="Chưa tải được thời gian sử dụng." action="Tải lại thời gian" onRetry={retry} />
        ) : week ? (
          <UsageColumnChart week={week} compact={compact} />
        ) : (
          <View style={styles.loadingBox}>
            <ActivityIndicator color={COLORS.primary} accessibilityLabel="Đang tải thời gian sử dụng" />
            <Text style={styles.body}>Đang đồng bộ thời gian sử dụng tuần này…</Text>
          </View>
        )}
      </View>
    </View>
  );
}

function UsageColumnChart({ week, compact }: { week: StudentUsageWeek; compact: boolean }) {
  const elapsedDays = week.days.filter(day => day.date <= week.today);
  if (elapsedDays.length === 0) return <Text style={styles.body}>Chưa có dữ liệu thời gian cho tuần này.</Text>;
  const max = Math.max(1, ...elapsedDays.map(day => day.elapsedMillis));

  return (
    <View style={[styles.columnChart, compact && styles.columnChartCompact]}>
      {week.days.map((day, index) => {
        const future = day.date > week.today;
        const today = day.date === week.today;
        const dayName = WEEKDAYS[index] ?? `N${index + 1}`;
        const valueLabel = future ? '—' : formatChartDayValue(day.elapsedMillis);
        const description = future ? 'Chưa tới' : formatUsage(day.elapsedMillis);
        const barHeight = !future && day.elapsedMillis > 0 ? Math.max(8, Math.round((86 * day.elapsedMillis) / max)) : 4;

        if (compact) return (
          <View key={day.date} accessible accessibilityLabel={`${dayName}${today ? ', hôm nay' : ''}, ${description}`}
            style={[styles.chartRow, today && styles.chartColToday]}>
            <Text style={[styles.chartRowDay, today && styles.chartColTodayText]}>{today ? 'Hôm nay' : dayName}</Text>
            <View style={styles.chartRowTrack} accessible={false} aria-hidden>
              {!future && day.elapsedMillis > 0 && (
                <View style={[styles.chartRowBar, today && styles.chartColBarToday,
                  { width: `${Math.max(4, (100 * day.elapsedMillis) / max)}%` }]} />
              )}
            </View>
            <Text style={[styles.chartRowValue, today && styles.chartColTodayText]}>{future ? '—' : description}</Text>
          </View>
        );

        return (
          <View
            key={day.date}
            accessible
            accessibilityLabel={`${today ? 'Hôm nay' : dayName}, ${description}`}
            style={[styles.chartCol, today && styles.chartColToday]}
          >
            <Text
              numberOfLines={1}
              style={[
                styles.chartColValue,
                !future && day.elapsedMillis === 0 && styles.chartColZeroText,
                today && styles.chartColTodayText,
              ]}
            >
              {valueLabel}
            </Text>
            <View style={[styles.chartColTrack, today && styles.chartColTrackToday]} accessible={false} aria-hidden>
              {!future && (
                <View
                  style={[
                    styles.chartColBar,
                    day.elapsedMillis === 0 && styles.chartColBarZero,
                    today && day.elapsedMillis > 0 && styles.chartColBarToday,
                    { height: barHeight },
                  ]}
                />
              )}
            </View>
            <Text style={[styles.chartColDay, today && styles.chartColTodayText]}>{dayName}</Text>
            <View style={styles.todaySlot}>
              {today ? (
                <View style={styles.todayPill}>
                  <Text style={styles.todayPillText}>Hôm nay</Text>
                </View>
              ) : null}
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  overviewRoot: { gap: 18 },
  heroBanner: {
    borderRadius: 22,
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
    padding: 18,
    gap: 16,
  },
  heroBannerWide: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 22,
    paddingVertical: 20,
  },
  heroIdentityRow: { flexDirection: 'row', alignItems: 'center', gap: 14, flex: 1, minWidth: 0 },
  heroAvatarWrap: {
    padding: 4,
    borderRadius: 40,
    backgroundColor: '#FFFFFFC8',
  },
  identityCopy: { flex: 1, minWidth: 0, gap: 3 },
  heroBadgeRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 6 },
  heroRolePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#FFFFFFD8',
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 999,
  },
  heroRoleText: { fontFamily: FONTS.extraBold, fontSize: 12, color: STUDENT_WEB.primary },
  heroStarPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFF3C6',
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 999,
  },
  heroStarText: { fontFamily: FONTS.extraBold, fontSize: 12, color: '#724C00' },
  heroName: { fontFamily: FONTS.black, fontSize: 22, lineHeight: 28, color: STUDENT_WEB.ink },
  heroNameCompact: { fontSize: 19, lineHeight: 25 },
  heroMeta: { fontFamily: FONTS.semiBold, fontSize: 13, color: STUDENT_WEB.muted },
  heroQuickPills: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  heroQuickPillsWide: { justifyContent: 'flex-end' },
  heroStatPill: {
    flexGrow: 1,
    minWidth: 140,
    backgroundColor: '#FFFFFFCC',
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
    gap: 2,
  },
  heroLimitPill: { backgroundColor: '#FFFFFF' },
  heroStatLabel: { fontFamily: FONTS.bold, fontSize: 12, color: STUDENT_WEB.muted },
  heroStatValue: { fontFamily: FONTS.black, fontSize: 17, color: STUDENT_WEB.ink },
  heroLimitValueRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 6 },
  heroLimitValue: { color: STUDENT_WEB.primary },
  pressed: { opacity: 0.78 },

  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  metricsDesktop: { flexWrap: 'nowrap', gap: 14 },
  metric: {
    minWidth: 0,
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  metricOneCol: { width: '100%', flexBasis: '100%' },
  metricTwoCol: { flexGrow: 1, flexBasis: '46%' },
  metricDesktop: { flex: 1, flexBasis: 0 },
  metricIcon: {
    width: 46,
    height: 46,
    borderRadius: 14,
    borderWidth: 1,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  metricArt: { width: 34, height: 34 },
  metricCopy: { flex: 1, minWidth: 0, gap: 2 },
  metricLabel: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.textSecondary },
  metricValue: { fontFamily: FONTS.black, fontSize: 21, lineHeight: 26, color: STUDENT_WEB.ink },
  metricSub: { fontFamily: FONTS.semiBold, fontSize: 12, color: STUDENT_WEB.muted },

  columns: { gap: 16 },
  columnsWide: { flexDirection: 'row', alignItems: 'stretch', gap: 18 },
  primaryChartColumn: { flex: 1.35 },
  secondaryChartColumn: { flex: 1 },
  equalColumn: { flex: 1 },

  panel: {
    minWidth: 0,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
    borderRadius: 22,
    padding: 18,
    gap: 16,
    ...(Platform.OS === 'web' ? { boxShadow: '0 6px 22px rgba(33, 23, 89, 0.04)' } : {}),
  },
  panelHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' },
  iconWell: {
    width: 44,
    height: 44,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: STUDENT_WEB.soft,
  },
  safeIcon: { backgroundColor: COLORS.pastelGreen },
  heading: { fontFamily: FONTS.extraBold, fontSize: 19, lineHeight: 25, color: STUDENT_WEB.ink },
  panelSubtitle: { fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 19, color: STUDENT_WEB.muted },
  panelBadge: {
    backgroundColor: STUDENT_WEB.soft,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  panelBadgeText: { fontFamily: FONTS.extraBold, fontSize: 12, color: STUDENT_WEB.primary },

  usageWrap: { gap: 14 },
  weeklyHighlightCard: {
    backgroundColor: '#F5F2FF',
    borderWidth: 1,
    borderColor: '#DDD6FE',
    borderRadius: 18,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 10,
  },
  weeklyHighlightMain: { gap: 2, flex: 1, minWidth: 150 },
  weeklyHighlightLabel: { fontFamily: FONTS.extraBold, fontSize: 11, color: STUDENT_WEB.primary, letterSpacing: 0.4 },
  weeklyHighlightValue: { fontFamily: FONTS.black, fontSize: 25, lineHeight: 31, color: STUDENT_WEB.ink },
  weeklyHighlightToday: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#DDD6FE',
    borderRadius: 14,
    paddingHorizontal: 13,
    paddingVertical: 8,
    gap: 2,
  },
  weeklyHighlightTodayLabel: { fontFamily: FONTS.bold, fontSize: 12, color: STUDENT_WEB.muted },
  weeklyHighlightTodayValue: { fontFamily: FONTS.black, fontSize: 16, color: STUDENT_WEB.primary },

  safeFacts: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 10 },
  fact: {
    flex: 1,
    minWidth: 180,
    backgroundColor: COLORS.pastelGreen,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: 16,
    padding: 13,
    gap: 4,
  },
  factLabel: { fontFamily: FONTS.bold, fontSize: 12, color: '#166534' },
  factValue: { fontFamily: FONTS.black, fontSize: 18, color: '#14532D' },
  limitProgressWrap: { gap: 5, marginTop: 4 },
  limitProgressTrack: { height: 7, borderRadius: 6, backgroundColor: '#DCFCE7', overflow: 'hidden' },
  limitProgressFill: { height: 7, borderRadius: 6 },
  limitProgressText: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#166534' },
  editLimitBtn: { minHeight: 48, paddingHorizontal: 16 },

  group: { gap: 10, paddingTop: 14, borderTopWidth: 1, borderTopColor: STUDENT_WEB.border },
  sectionLabel: { fontFamily: FONTS.extraBold, fontSize: 15, color: STUDENT_WEB.ink },
  chartSubHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 6 },

  columnChart: { flexDirection: 'row', gap: 6, alignItems: 'stretch' },
  columnChartCompact: { flexDirection: 'column', gap: 5 },
  chartRow: {
    flexDirection: 'row', alignItems: 'center', minHeight: 36, gap: 8,
    paddingHorizontal: 8, paddingVertical: 5, borderRadius: 10,
    borderWidth: 1, borderColor: '#EFEBF9', backgroundColor: '#FAF9FF',
  },
  chartRowDay: { flexBasis: 53, fontFamily: FONTS.extraBold, fontSize: 12, color: STUDENT_WEB.muted },
  chartRowTrack: { flex: 1, height: 7, borderRadius: 4, backgroundColor: '#E7E1F4', overflow: 'hidden' },
  chartRowBar: { height: '100%', borderRadius: 4, backgroundColor: '#8B75F8' },
  chartRowValue: { flexBasis: 94, textAlign: 'right', fontFamily: FONTS.bold, fontSize: 12, color: STUDENT_WEB.ink },
  chartCol: {
    flex: 1,
    minWidth: 0,
    borderRadius: 14,
    paddingVertical: 8,
    paddingHorizontal: 3,
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FAF9FF',
    borderWidth: 1,
    borderColor: '#EFEBF9',
  },
  chartColToday: { backgroundColor: COLORS.primaryLight, borderColor: STUDENT_WEB.primary },
  chartColValue: { fontFamily: FONTS.bold, fontSize: 11, color: STUDENT_WEB.muted, textAlign: 'center' },
  chartColZeroText: { color: COLORS.textMuted },
  chartColTodayText: { color: STUDENT_WEB.primary, fontFamily: FONTS.black },
  chartColTrack: {
    height: 90,
    width: '68%',
    maxWidth: 32,
    borderRadius: 8,
    backgroundColor: '#EEF2F6',
    justifyContent: 'flex-end',
    padding: 2,
  },
  chartColTrackToday: { backgroundColor: '#FFFFFF' },
  chartColBar: { width: '100%', backgroundColor: '#8B75F8', borderRadius: 5 },
  chartColBarToday: { backgroundColor: STUDENT_WEB.primary },
  chartColBarZero: { backgroundColor: '#CBD5E1', borderRadius: 2 },
  chartColDay: { fontFamily: FONTS.extraBold, fontSize: 12, color: STUDENT_WEB.muted },
  todaySlot: { minHeight: 16, justifyContent: 'center', alignItems: 'center' },
  todayPill: { backgroundColor: STUDENT_WEB.primary, borderRadius: 6, paddingHorizontal: 5, paddingVertical: 1 },
  todayPillText: { fontFamily: FONTS.extraBold, fontSize: 9, color: '#FFFFFF' },

  progressBody: { gap: 14 },
  distList: { gap: 10 },
  distItem: { gap: 5 },
  distTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  distLabel: { fontFamily: FONTS.bold, fontSize: 14, color: STUDENT_WEB.ink },
  distCount: { fontFamily: FONTS.extraBold, fontSize: 13, color: STUDENT_WEB.primary },
  distTrack: { height: 10, borderRadius: 6, overflow: 'hidden' },
  distFill: { height: 10, borderRadius: 6 },

  miniChart: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'flex-end',
    backgroundColor: '#FAF9FF',
    borderRadius: 14,
    padding: 10,
    borderWidth: 1,
    borderColor: '#EFEBF9',
  },
  miniCol: { flex: 1, minWidth: 0, alignItems: 'center', gap: 4 },
  miniCount: { fontFamily: FONTS.extraBold, fontSize: 12, color: STUDENT_WEB.primary },
  miniTrack: { height: 48, width: '70%', maxWidth: 24, justifyContent: 'flex-end', alignItems: 'center' },
  miniBar: { width: '100%', borderRadius: 5 },
  miniLabel: { fontFamily: FONTS.bold, fontSize: 11, color: STUDENT_WEB.muted, textAlign: 'center' },

  feedList: { gap: 10 },
  feedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 11,
    borderRadius: 14,
    backgroundColor: '#FAF9FF',
    borderWidth: 1,
    borderColor: '#EFEBF9',
  },
  feedIcon: { width: 38, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  feedTitle: { fontFamily: FONTS.extraBold, fontSize: 14, color: STUDENT_WEB.ink },
  feedDate: { fontFamily: FONTS.semiBold, fontSize: 12, color: STUDENT_WEB.muted },
  feedStarBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFF3C6',
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 999,
  },
  feedStarText: { fontFamily: FONTS.extraBold, fontSize: 12, color: '#724C00' },

  summaryTiles: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  summaryTile: {
    flexGrow: 1,
    flexBasis: '45%',
    minWidth: 130,
    backgroundColor: '#FAF9FF',
    borderWidth: 1,
    borderColor: '#EFEBF9',
    borderRadius: 16,
    padding: 13,
    gap: 4,
  },
  summaryTileLabel: { fontFamily: FONTS.bold, fontSize: 13, color: STUDENT_WEB.muted },
  summaryTileValue: { fontFamily: FONTS.black, fontSize: 22, color: STUDENT_WEB.ink },

  guide: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 13,
    borderRadius: 14,
    backgroundColor: COLORS.pastelAmber,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  guideIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  guideCopy: { flex: 1, minWidth: 0, gap: 2 },
  guideTitle: { fontFamily: FONTS.extraBold, fontSize: 14, color: '#92400E' },

  empty: {
    gap: 6,
    padding: 16,
    backgroundColor: '#FAF9FF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#EFEBF9',
    alignItems: 'flex-start',
  },
  loadingBox: { alignItems: 'center', justifyContent: 'center', paddingVertical: 20, gap: 10 },
  errorCard: {
    gap: 8,
    padding: 14,
    borderRadius: 16,
    backgroundColor: '#FFF8F6',
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  errorTitle: { fontFamily: FONTS.extraBold, fontSize: 15, color: COLORS.errorText },
  label: { fontFamily: FONTS.extraBold, fontSize: 16, color: STUDENT_WEB.ink },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 21, color: STUDENT_WEB.muted },
});
