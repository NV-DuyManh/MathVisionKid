import React, { useContext } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppCard } from '../../components/ui/AppCard';
import { AuthContext } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';

import { isHandAIMode } from '../../config/appMode';

export default function ProfileScreen() {
  const isHandAI = isHandAIMode();
  const auth = useContext(AuthContext);
  const user = auth?.user;

  const handleLogout = () => {
    Alert.alert(
      'Đăng xuất',
      'Em có chắc chắn muốn đăng xuất không?',
      [
        { text: 'Hủy', style: 'cancel' },
        { text: 'Đăng xuất', style: 'destructive', onPress: () => auth?.logout() },
      ]
    );
  };

  if (isHandAI) {
    return (
      <View style={styles.container}>
        <AppHeader title="Recognition History" />
        <ScrollView contentContainerStyle={styles.content}>
          {/* Research Dataset & System Specification Card */}
          <AppCard style={styles.researchCard} variant="elevated">
            <View style={styles.researchHeaderRow}>
              <View style={styles.researchIconContainer}>
                <Ionicons name="analytics" size={28} color="#2563EB" />
              </View>
              <View style={styles.researchTitleContainer}>
                <Text style={styles.researchTitle}>HandAI Research System</Text>
                <Text style={styles.researchSubtitle}>Grade 1-5 Student Handwriting Dataset</Text>
              </View>
            </View>

            <View style={styles.researchMetaGrid}>
              <View style={styles.researchMetaItem}>
                <Text style={styles.researchMetaLabel}>Domain</Text>
                <Text style={styles.researchMetaValue}>Primary Handwriting</Text>
              </View>
              <View style={styles.researchMetaItem}>
                <Text style={styles.researchMetaLabel}>Scope</Text>
                <Text style={styles.researchMetaValue}>Grade 1-5 Vietnamese</Text>
              </View>
              <View style={styles.researchMetaItem}>
                <Text style={styles.researchMetaLabel}>Model</Text>
                <Text style={styles.researchMetaValue}>CRNN + CTC Softmax</Text>
              </View>
              <View style={styles.researchMetaItem}>
                <Text style={styles.researchMetaLabel}>Arbitration</Text>
                <Text style={styles.researchMetaValue}>Multi-Provider Consensus</Text>
              </View>
            </View>
          </AppCard>

          {/* Pipeline Specifications */}
          <AppCard style={styles.researchCard} variant="outlined">
            <Text style={styles.researchSectionTitle}>Processing Pipeline</Text>
            <View style={styles.pipelineList}>
              {[
                { step: '1', title: 'Image Acquisition', desc: 'Direct camera / photo library acquisition' },
                { step: '2', title: 'Preprocessing', desc: 'Perspective notebook crop and orientation normalization' },
                { step: '3', title: 'Line Segmentation', desc: 'Multi-line bounding box detection and ordering' },
                { step: '4', title: 'Handwriting Recognition', desc: 'CRNN sequence predictor with CTC softmax' },
                { step: '5', title: 'Result Analysis', desc: 'Candidate arbitration and transparent decision display' },
              ].map((item) => (
                <View key={item.step} style={styles.pipelineStepRow}>
                  <View style={styles.pipelineStepBadge}>
                    <Text style={styles.pipelineStepBadgeText}>{item.step}</Text>
                  </View>
                  <View style={styles.pipelineStepContent}>
                    <Text style={styles.pipelineStepTitle}>{item.title}</Text>
                    <Text style={styles.pipelineStepDesc}>{item.desc}</Text>
                  </View>
                </View>
              ))}
            </View>
          </AppCard>

          {/* Session Trial Status */}
          <AppCard style={styles.researchCard} variant="outlined">
            <Text style={styles.researchSectionTitle}>Session Benchmark Trials</Text>
            <View style={styles.emptyTrialsContainer}>
              <Ionicons name="time-outline" size={36} color="#94A3B8" />
              <Text style={styles.emptyTrialsTitle}>Ready for Evaluation</Text>
              <Text style={styles.emptyTrialsDesc}>
                Acquire or upload notebook images from Home or Scan to execute the handwriting recognition pipeline.
              </Text>
            </View>
          </AppCard>
        </ScrollView>
      </View>
    );
  }

  const menuItems = [
    {
      icon: 'shield-checkmark-outline' as const,
      label: 'Bảo mật & Dữ liệu riêng tư',
      sublabel: 'Ảnh được bảo vệ theo chuẩn riêng tư',
    },
    {
      icon: 'language-outline' as const,
      label: 'Ngôn ngữ hiển thị',
      sublabel: 'Tiếng Việt',
    },
    {
      icon: 'help-circle-outline' as const,
      label: 'Hướng dẫn sử dụng',
      sublabel: 'Cách chụp bài rõ nét',
    },
    {
      icon: 'information-circle-outline' as const,
      label: 'Thông tin ứng dụng',
      sublabel: 'MathVision Kids v1.0.0',
    },
  ];

  return (
    <View style={styles.container}>
      <AppHeader title="Hồ sơ của em" />
      <ScrollView contentContainerStyle={styles.content}>
        {/* Student identity card */}
        <AppCard style={styles.card} variant="elevated">
          <View style={[styles.avatarBadge, SHADOWS.small]}>
            <Ionicons name="school" size={36} color={COLORS.primary} />
          </View>
          <Text style={styles.name}>{user?.name || user?.email || 'Học sinh'}</Text>
          <View style={styles.gradePill}>
            <Text style={styles.gradeText}>
              {user?.grade ? `Học sinh Lớp ${user.grade}` : 'Học sinh Tiểu học'}
            </Text>
          </View>
        </AppCard>

        {/* Menu items card */}
        <AppCard style={styles.menuCard} variant="outlined">
          {menuItems.map((item, index) => (
            <View key={item.label}>
              <View style={styles.menuItem}>
                <View style={styles.menuIconContainer}>
                  <Ionicons name={item.icon} size={22} color={COLORS.primary} />
                </View>
                <View style={styles.menuTextContainer}>
                  <Text style={styles.menuLabel}>{item.label}</Text>
                  <Text style={styles.menuSublabel}>{item.sublabel}</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={COLORS.textMuted} />
              </View>
              {index < menuItems.length - 1 && <View style={styles.divider} />}
            </View>
          ))}
        </AppCard>

        {/* Logout button */}
        <TouchableOpacity
          style={styles.logoutButton}
          onPress={handleLogout}
          accessibilityRole="button"
          accessibilityLabel="Đăng xuất khỏi ứng dụng"
        >
          <Ionicons name="log-out-outline" size={22} color={COLORS.error} />
          <Text style={styles.logoutText}>Đăng xuất</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.medium,
    paddingBottom: SIZES.xxlarge,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  card: {
    alignItems: 'center',
    paddingVertical: SIZES.xxlarge,
    marginBottom: SIZES.large,
  },
  avatarBadge: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: COLORS.surfaceSubdued,
    borderWidth: 2,
    borderColor: '#BFDBFE',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SIZES.medium,
  },
  name: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 6,
  },
  gradePill: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: SIZES.medium,
    paddingVertical: 4,
    borderRadius: SIZES.pillRadius,
  },
  gradeText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primary,
  },
  menuCard: {
    padding: 0,
    overflow: 'hidden',
    marginBottom: SIZES.xlarge,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SIZES.medium,
    minHeight: SIZES.minTouchTarget,
  },
  menuIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.surfaceSubdued,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SIZES.medium,
  },
  menuTextContainer: {
    flex: 1,
  },
  menuLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 2,
  },
  menuSublabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginLeft: 56,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: SIZES.minTouchTarget,
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: SIZES.buttonRadius,
    paddingHorizontal: SIZES.large,
  },
  logoutText: {
    marginLeft: SIZES.small,
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.error,
  },
  // HandAI Research Demo V3 styles
  researchCard: {
    marginBottom: SIZES.large,
    padding: SIZES.large,
  },
  researchHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SIZES.medium,
    gap: 12,
  },
  researchIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#EFF6FF',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  researchTitleContainer: {
    flex: 1,
  },
  researchTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  researchSubtitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
    marginTop: 2,
  },
  researchMetaGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 4,
  },
  researchMetaItem: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  researchMetaLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  researchMetaValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
  },
  researchSectionTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: SIZES.medium,
  },
  pipelineList: {
    gap: 12,
  },
  pipelineStepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  pipelineStepBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#2563EB',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 2,
  },
  pipelineStepBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  pipelineStepContent: {
    flex: 1,
  },
  pipelineStepTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
  },
  pipelineStepDesc: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
    lineHeight: 16,
  },
  emptyTrialsContainer: {
    alignItems: 'center',
    paddingVertical: SIZES.large,
    gap: 8,
  },
  emptyTrialsTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#334155',
  },
  emptyTrialsDesc: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 18,
    maxWidth: 320,
  },
});
