import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { AppHeader } from '../components/ui/AppHeader';
import {
  handAiAnalyticsStore,
  RecognitionSession,
  AnalyticsSummary,
} from '../services/analytics/handAiAnalyticsStore';

const PRIMARY_COLOR = '#123B7A';
const SECONDARY_COLOR = '#2563EB';
const BG_COLOR = '#F8FAFC';

export default function HandAiAnalyticsScreen() {
  const router = useRouter();
  const [sessions, setSessions] = useState<RecognitionSession[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [sources, setSources] = useState<{ label: string; count: number; percent: number; color: string }[]>([]);
  const [confidenceBuckets, setConfidenceBuckets] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    await handAiAnalyticsStore.init();
    setSessions(handAiAnalyticsStore.getSessions());
    setSummary(handAiAnalyticsStore.getSummary());
    setSources(handAiAnalyticsStore.getSourceDistribution());
    setConfidenceBuckets(handAiAnalyticsStore.getConfidenceDistribution());
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <AppHeader title="HandAI Accuracy Analytics" showBack />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Academic Header Banner */}
        <View style={styles.headerBanner}>
          <View style={styles.headerBadgeRow}>
            <View style={styles.headerPill}>
              <View style={styles.headerPillDot} />
              <Text style={styles.headerPillText}>HAND_AI BIG DATA MODULE</Text>
            </View>
            <Text style={styles.sampleCountText}>
              {summary ? `${summary.totalSessions} Sessions • ${summary.totalLinesProcessed} Lines` : ''}
            </Text>
          </View>
          <Text style={styles.bannerTitle}>Recognition Quality Evaluation</Text>
          <Text style={styles.bannerSubtitle}>
            Continuous validation metrics across CRNN model output and AI spelling correction arbitration.
          </Text>
        </View>

        {/* 4 Core Metrics Grid */}
        <View style={styles.kpiGrid}>
          {/* 1. Accuracy % */}
          <View style={styles.kpiCard}>
            <View style={styles.kpiIconWrapper}>
              <Ionicons name="checkmark-done-circle" size={20} color="#22C55E" />
            </View>
            <Text style={styles.kpiValue}>
              {summary ? `${summary.accuracyPercent}%` : '--%'}
            </Text>
            <Text style={styles.kpiLabel}>Recognition Accuracy</Text>
            <Text style={styles.kpiFormula}>correct / total * 100</Text>
          </View>

          {/* 2. Average Confidence */}
          <View style={styles.kpiCard}>
            <View style={[styles.kpiIconWrapper, { backgroundColor: '#EFF6FF' }]}>
              <Ionicons name="speedometer-outline" size={20} color={SECONDARY_COLOR} />
            </View>
            <Text style={styles.kpiValue}>
              {summary ? `${summary.averageConfidence}%` : '--%'}
            </Text>
            <Text style={styles.kpiLabel}>Avg. Confidence</Text>
            <Text style={styles.kpiFormula}>Model certainty score</Text>
          </View>

          {/* 3. AI Correction Rate */}
          <View style={styles.kpiCard}>
            <View style={[styles.kpiIconWrapper, { backgroundColor: '#FEF3C7' }]}>
              <Ionicons name="sparkles" size={20} color="#D97706" />
            </View>
            <Text style={styles.kpiValue}>
              {summary ? `${summary.aiCorrectionRate}%` : '--%'}
            </Text>
            <Text style={styles.kpiLabel}>AI Correction Rate</Text>
            <Text style={styles.kpiFormula}>Candidate substitutions</Text>
          </View>

          {/* 4. OCR Accepted Rate */}
          <View style={styles.kpiCard}>
            <View style={[styles.kpiIconWrapper, { backgroundColor: '#F1F5F9' }]}>
              <Ionicons name="document-text-outline" size={20} color="#475569" />
            </View>
            <Text style={styles.kpiValue}>
              {summary ? `${summary.ocrAcceptedRate}%` : '--%'}
            </Text>
            <Text style={styles.kpiLabel}>OCR Accepted Rate</Text>
            <Text style={styles.kpiFormula}>Raw model direct match</Text>
          </View>
        </View>

        {/* Chart A: Accuracy Trend Chart */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Ionicons name="trending-up-outline" size={18} color={PRIMARY_COLOR} />
            <Text style={styles.sectionTitle}>Accuracy Trend Chart</Text>
          </View>
          <Text style={styles.sectionSubtitle}>
            Progression across sequential handwriting evaluation trials
          </Text>

          <View style={styles.trendList}>
            {sessions.map((s, idx) => (
              <View key={idx} style={styles.trendRow}>
                <View style={styles.trendLabelContainer}>
                  <Text style={styles.trendSessionText}>{s.dateStr}</Text>
                  <Text style={styles.trendDetailText}>({s.correctLines}/{s.totalLines} lines)</Text>
                </View>
                <View style={styles.trendBarTrack}>
                  <View
                    style={[
                      styles.trendBarFill,
                      {
                        width: `${s.accuracy}%`,
                        backgroundColor: s.accuracy >= 90 ? '#10B981' : s.accuracy >= 80 ? SECONDARY_COLOR : '#F59E0B',
                      },
                    ]}
                  />
                </View>
                <Text style={styles.trendPercentText}>{s.accuracy}%</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Chart B: Recognition Source Breakdown */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Ionicons name="pie-chart-outline" size={18} color={PRIMARY_COLOR} />
            <Text style={styles.sectionTitle}>Recognition Source Distribution</Text>
          </View>
          <Text style={styles.sectionSubtitle}>
            Proportion of final confirmed characters by decision engine
          </Text>

          {/* Stacked Proportional Bar */}
          <View style={styles.stackedBarContainer}>
            {sources.map((src, idx) => (
              <View
                key={idx}
                style={[
                  styles.stackedBarSegment,
                  {
                    width: `${Math.max(4, src.percent)}%`,
                    backgroundColor: src.color,
                  },
                ]}
              />
            ))}
          </View>

          {/* Legend Items */}
          <View style={styles.legendContainer}>
            {sources.map((src, idx) => (
              <View key={idx} style={styles.legendItem}>
                <View style={[styles.legendColorDot, { backgroundColor: src.color }]} />
                <View style={styles.legendTextGroup}>
                  <Text style={styles.legendLabel}>{src.label}</Text>
                  <Text style={styles.legendCount}>
                    {src.count} lines ({src.percent}%)
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* Chart C: Confidence Distribution */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Ionicons name="bar-chart-outline" size={18} color={PRIMARY_COLOR} />
            <Text style={styles.sectionTitle}>Confidence Score Distribution</Text>
          </View>
          <Text style={styles.sectionSubtitle}>
            Distribution across high, medium, and low model confidence thresholds
          </Text>

          <View style={styles.confidenceList}>
            {confidenceBuckets.map((bucket, idx) => (
              <View key={idx} style={styles.confidenceItem}>
                <View style={styles.confidenceHeaderRow}>
                  <Text style={styles.confidenceLabel}>{bucket.label}</Text>
                  <Text style={styles.confidenceRange}>{bucket.range}</Text>
                  <Text style={styles.confidenceCount}>{bucket.percent}% ({bucket.count} trials)</Text>
                </View>
                <View style={styles.trendBarTrack}>
                  <View
                    style={[
                      styles.trendBarFill,
                      {
                        width: `${bucket.percent}%`,
                        backgroundColor: bucket.color,
                      },
                    ]}
                  />
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* Navigation Action */}
        <TouchableOpacity
          style={styles.backActionBtn}
          onPress={() => router.back()}
          accessibilityRole="button"
          accessibilityLabel="Back to Review"
        >
          <Ionicons name="arrow-back" size={18} color="#FFFFFF" />
          <Text style={styles.backActionBtnText}>Back to Handwriting Evaluation</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: BG_COLOR,
  },
  container: {
    flex: 1,
    backgroundColor: BG_COLOR,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
    gap: 16,
  },
  headerBanner: {
    backgroundColor: PRIMARY_COLOR,
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  headerBadgeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  headerPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    gap: 6,
  },
  headerPillDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#38BDF8',
  },
  headerPillText: {
    color: '#38BDF8',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  sampleCountText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '500',
  },
  bannerTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  bannerSubtitle: {
    color: '#CBD5E1',
    fontSize: 12,
    lineHeight: 18,
  },
  /* KPI Grid */
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  kpiCard: {
    flex: 1,
    minWidth: '47%',
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  kpiIconWrapper: {
    width: 32,
    height: 32,
    borderRadius: 6,
    backgroundColor: '#DCFCE7',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  kpiValue: {
    fontSize: 22,
    fontWeight: '800',
    color: PRIMARY_COLOR,
    marginBottom: 2,
  },
  kpiLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
  },
  kpiFormula: {
    fontSize: 10,
    color: '#94A3B8',
    marginTop: 2,
  },
  /* Sections */
  sectionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 2,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: PRIMARY_COLOR,
  },
  sectionSubtitle: {
    fontSize: 11,
    color: '#64748B',
    marginBottom: 14,
  },
  /* Trend Chart */
  trendList: {
    gap: 10,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  trendLabelContainer: {
    width: 90,
  },
  trendSessionText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
  },
  trendDetailText: {
    fontSize: 10,
    color: '#94A3B8',
  },
  trendBarTrack: {
    flex: 1,
    height: 12,
    backgroundColor: '#F1F5F9',
    borderRadius: 3,
    overflow: 'hidden',
  },
  trendBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  trendPercentText: {
    width: 38,
    textAlign: 'right',
    fontSize: 12,
    fontWeight: '700',
    color: PRIMARY_COLOR,
  },
  /* Stacked Bar */
  stackedBarContainer: {
    flexDirection: 'row',
    height: 16,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 14,
  },
  stackedBarSegment: {
    height: '100%',
  },
  legendContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 8,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendColorDot: {
    width: 10,
    height: 10,
    borderRadius: 2,
  },
  legendTextGroup: {
    gap: 1,
  },
  legendLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
  },
  legendCount: {
    fontSize: 10,
    color: '#64748B',
  },
  /* Confidence list */
  confidenceList: {
    gap: 12,
  },
  confidenceItem: {
    gap: 4,
  },
  confidenceHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  confidenceLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1E293B',
  },
  confidenceRange: {
    fontSize: 10,
    color: '#64748B',
    fontStyle: 'italic',
  },
  confidenceCount: {
    fontSize: 11,
    fontWeight: '700',
    color: PRIMARY_COLOR,
  },
  /* Back Action */
  backActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: PRIMARY_COLOR,
    height: 48,
    borderRadius: 8,
    gap: 8,
    marginTop: 8,
  },
  backActionBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});
