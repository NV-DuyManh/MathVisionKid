import React, { useContext } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppCard } from '../../components/ui/AppCard';
import { AuthContext } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { RecognitionService } from '../../features/recognition/api/RecognitionService';
import { evaluateMathSolution } from '../../utils/mathSolutionEvaluator';
export default function ProfileScreen() {
    const router = useRouter();
    const auth = useContext(AuthContext);
    const user = auth?.user;
    const trials = RecognitionService.getAllCachedTrials();
    const handleLogout = () => {
        Alert.alert('Đăng xuất', 'Em có chắc chắn muốn đăng xuất không?', [
            { text: 'Hủy', style: 'cancel' },
            { text: 'Đăng xuất', style: 'destructive', onPress: () => auth?.logout() }
        ]);
    };
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
        }
    ];
    return (<View style={styles.container}>
      <AppHeader title="Hồ sơ của em"/>
      <ScrollView contentContainerStyle={styles.content}>
        <TouchableOpacity style={[styles.sessionCard, SHADOWS.small]} onPress={() => router.push('/recognition/analytics')} accessibilityRole="button" accessibilityLabel="Xem lịch sử nhận dạng">
          <Text style={styles.sectionHeadingTitle}>Lịch sử nhận dạng</Text>
          <Text style={styles.emptyResearchSubtitle}>Xem các dòng chữ đã xác nhận và xuất kết quả.</Text>
        </TouchableOpacity>
        {/* Student identity card */}
        <AppCard style={styles.card} variant="elevated">
          <View style={[styles.avatarBadge, SHADOWS.small]}>
            <Ionicons name="school" size={36} color={COLORS.primary}/>
          </View>
          <Text style={styles.name}>{user?.name || user?.email || 'Học sinh'}</Text>
          <View style={styles.gradePill}>
            <Text style={styles.gradeText}>
              {user?.grade ? `Học sinh Lớp ${user.grade}` : 'Học sinh Tiểu học'}
            </Text>
          </View>
        </AppCard>

        {/* Section: Recent Graded Math Worksheets */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionHeadingTitle}>Bài giải toán đã chấm</Text>
          <Text style={styles.sessionCountTag}>{trials.length} bài làm</Text>
        </View>

        {trials.length === 0 ? (<View style={[styles.emptyResearchCard, SHADOWS.small, { marginBottom: SIZES.large }]}>
            <View style={styles.emptyIconWrapper}>
              <Ionicons name="school-outline" size={34} color={COLORS.primary}/>
            </View>
            <Text style={styles.emptyResearchTitle}>Chưa có bài giải nào</Text>
            <Text style={styles.emptyResearchSubtitle}>
              Hãy chụp bài giải toán viết tay để MathVision chấm điểm, kiểm tra phép tính và gợi ý cách giải nhé!
            </Text>
            <TouchableOpacity style={[styles.emptyStartBtn, SHADOWS.small]} onPress={() => router.push('/camera' as any)} activeOpacity={0.88} accessibilityRole="button" accessibilityLabel="Chụp bài giải ngay">
              <Ionicons name="camera-outline" size={18} color="#FFFFFF"/>
              <Text style={styles.emptyStartBtnText}>Chụp bài giải ngay</Text>
            </TouchableOpacity>
          </View>) : (<View style={[styles.trialsList, { marginBottom: SIZES.large }]}>
            {trials.map((trial, index) => {
                const evalRes = trial.lines ? evaluateMathSolution(trial.lines) : null;
                const summary = evalRes?.summary;
                const isAllCorrect = summary?.verdict === 'ALL_CORRECT';
                const hasCalcError = summary?.verdict === 'HAS_CALCULATION_ERROR';
                const badgeBg = isAllCorrect ? '#DCFCE7' : hasCalcError ? '#FEF3C7' : '#EFF6FF';
                const badgeColor = isAllCorrect ? '#15803D' : hasCalcError ? '#B45309' : '#1E40AF';
                const badgeText = isAllCorrect
                    ? 'Đúng toàn bộ 🎉'
                    : hasCalcError
                        ? 'Cần sửa lại 💡'
                        : 'Chữ viết tay 📝';
                return (<TouchableOpacity key={trial.trialId || index} style={[styles.sessionCard, SHADOWS.small]} onPress={() => router.push({
                        pathname: '/recognition/multiline-result' as any,
                        params: { trialId: trial.trialId },
                    })} activeOpacity={0.88} accessibilityRole="button" accessibilityLabel={`Bài làm ${index + 1}`}>
                  <View style={styles.sessionCardTop}>
                    <View style={styles.sessionBadge}>
                      <Ionicons name="document-text" size={14} color="#1E40AF"/>
                      <Text style={styles.sessionBadgeText}>Bài làm #{index + 1}</Text>
                    </View>
                    <View style={[styles.confidenceChip, { backgroundColor: badgeBg }]}>
                      <Text style={[styles.confidenceChipText, { color: badgeColor }]}>{badgeText}</Text>
                    </View>
                  </View>

                  <View style={styles.sessionMetricsRow}>
                    <View style={styles.sessionMetricItem}>
                      <Text style={styles.sessionMetricLabel}>Dòng chữ</Text>
                      <Text style={styles.sessionMetricValue}>{trial.lines?.length || 0} dòng</Text>
                    </View>
                    <View style={styles.sessionMetricItem}>
                      <Text style={styles.sessionMetricLabel}>Phép tính</Text>
                      <Text style={[
                        styles.sessionMetricValue,
                        {
                            color: isAllCorrect
                                ? '#15803D'
                                : hasCalcError
                                    ? '#DC2626'
                                    : COLORS.textPrimary,
                        }
                    ]}>
                        {summary?.equationCount
                        ? `${summary.correctEquations}/${summary.equationCount} đúng`
                        : 'Không có'}
                      </Text>
                    </View>
                    <View style={styles.sessionMetricItem}>
                      <Text style={styles.sessionMetricLabel}>Đáp số</Text>
                      <Text style={[
                        styles.sessionMetricValue,
                        { color: summary?.hasAnswer ? '#7C3AED' : '#94A3B8' }
                    ]}>
                        {summary?.hasAnswer ? 'Có ✓' : 'Chưa'}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.sessionCardFooter}>
                    <Text style={styles.viewResultText}>Xem chi tiết bài giải & lời phê</Text>
                    <Ionicons name="chevron-forward" size={16} color="#1E40AF"/>
                  </View>
                </TouchableOpacity>);
            })}
          </View>)}

        {/* Menu items card */}
        <AppCard style={styles.menuCard} variant="outlined">
          {menuItems.map((item, index) => (<View key={item.label}>
              <View style={styles.menuItem}>
                <View style={styles.menuIconContainer}>
                  <Ionicons name={item.icon} size={22} color={COLORS.primary}/>
                </View>
                <View style={styles.menuTextContainer}>
                  <Text style={styles.menuLabel}>{item.label}</Text>
                  <Text style={styles.menuSublabel}>{item.sublabel}</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={COLORS.textMuted}/>
              </View>
              {index < menuItems.length - 1 && <View style={styles.divider}/>}
            </View>))}
        </AppCard>

        {/* Logout button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout} accessibilityRole="button" accessibilityLabel="Đăng xuất khỏi ứng dụng">
          <Ionicons name="log-out-outline" size={22} color={COLORS.error}/>
          <Text style={styles.logoutText}>Đăng xuất</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>);
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
    sectionHeaderRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    sectionHeadingTitle: {
        fontSize: 15,
        fontWeight: '800',
        color: '#0F172A',
    },
    sessionCountTag: {
        fontSize: 12,
        fontWeight: '600',
        color: '#64748B',
    },
    emptyResearchCard: {
        backgroundColor: '#FFFFFF',
        borderRadius: 16,
        borderWidth: 1,
        borderColor: '#E2E8F0',
        padding: 24,
        alignItems: 'center',
    },
    emptyIconWrapper: {
        width: 64,
        height: 64,
        borderRadius: 32,
        backgroundColor: '#F8FAFC',
        borderWidth: 1,
        borderColor: '#E2E8F0',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 14,
    },
    emptyResearchTitle: {
        fontSize: 16,
        fontWeight: '800',
        color: '#0F172A',
        marginBottom: 6,
        textAlign: 'center',
    },
    emptyResearchSubtitle: {
        fontSize: 13,
        color: '#64748B',
        textAlign: 'center',
        lineHeight: 18,
        marginBottom: 18,
        maxWidth: 320,
    },
    emptyStartBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        backgroundColor: '#1E40AF',
        paddingVertical: 12,
        paddingHorizontal: 20,
        borderRadius: 12,
    },
    emptyStartBtnText: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: '700',
    },
    trialsList: {
        gap: 12,
    },
    sessionCard: {
        backgroundColor: '#FFFFFF',
        borderRadius: 14,
        padding: 16,
        borderWidth: 1,
        borderColor: '#E2E8F0',
    },
    sessionCardTop: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    sessionBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
    },
    sessionBadgeText: {
        fontSize: 13,
        fontWeight: '700',
        color: '#1E40AF',
    },
    confidenceChip: {
        backgroundColor: '#EFF6FF',
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: '#BFDBFE',
    },
    confidenceChipText: {
        fontSize: 11,
        fontWeight: '700',
        color: '#1E40AF',
    },
    sessionMetricsRow: {
        flexDirection: 'row',
        gap: 8,
        marginBottom: 12,
    },
    sessionMetricItem: {
        flex: 1,
        backgroundColor: '#F8FAFC',
        padding: 8,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#F1F5F9',
    },
    sessionMetricLabel: {
        fontSize: 10,
        fontWeight: '600',
        color: '#64748B',
        textTransform: 'uppercase',
    },
    sessionMetricValue: {
        fontSize: 13,
        fontWeight: '700',
        color: '#0F172A',
        marginTop: 2,
    },
    sessionCardFooter: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingTop: 10,
        borderTopWidth: 1,
        borderTopColor: '#F1F5F9',
    },
    viewResultText: {
        fontSize: 12,
        fontWeight: '700',
        color: '#1E40AF',
    },
});
