import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';
import { getSubmissionService } from '../../services/api/SubmissionServiceFactory';
import { SubmissionResult } from '../../types';
import { logFlowDomain } from '../../features/recognition/state/recognitionDraftStore';
import { resolveResultRoute } from '../../utils/resultRouting';

interface ReasonContent {
  title: string;
  subtitle: string;
  actionTitle: string;
}

function getReasonContent(reasonCode?: string): ReasonContent {
  switch (reasonCode) {
    case 'RESULT_UNCERTAIN':
      return {
        title: 'Chưa đủ dữ liệu để kết luận',
        subtitle: 'MathVision chưa thể kết luận bài đúng hay sai. Em hãy chụp lại ảnh rõ hơn hoặc nhờ thầy cô xem giúp nhé.',
        actionTitle: 'Chụp lại bài làm',
      };
    case 'DETECTOR_NO_TOKENS':
    case 'NO_CONTENT_DETECTED':
      return {
        title: 'MathVision chưa nhận diện được bài làm',
        subtitle: 'MathVision đã thử nhận diện nhưng chưa nhận ra đủ chữ số hoặc dấu phép tính trong ảnh.',
        actionTitle: 'Thử lại',
      };
    case 'INVALID_LAYOUT':
      return {
        title: 'Cần thầy cô xem cách đặt tính',
        subtitle: 'Các chữ số hoặc dấu phép tính chưa rõ ràng theo hàng dọc. Em hãy chụp lại hoặc nhờ thầy cô xem cách đặt tính nhé.',
        actionTitle: 'Thử lại',
      };
    case 'OCR_LOW_CONFIDENCE':
      return {
        title: 'MathVision chưa chắc chắn kết quả',
        subtitle: 'MathVision đã thử đọc bài của em nhưng chưa đủ chắc chắn để kết luận. Em hãy chụp lại rõ hơn hoặc nhờ thầy cô xem giúp nhé.',
        actionTitle: 'Thử lại',
      };
    case 'IMAGE_QUALITY_FAILED':
      return {
        title: 'Chất lượng ảnh chụp chưa đạt',
        subtitle: 'Ảnh chụp có thể bị chói sáng, quá tối hoặc bị che khuất. Em hãy chụp lại hoặc nhờ thầy cô xem giúp nhé.',
        actionTitle: 'Chụp lại ảnh mới',
      };
    case 'IMAGE_EFFECTIVELY_EMPTY':
      return {
        title: 'Ảnh chụp chưa có bài làm',
        subtitle: 'Ảnh chụp có vẻ còn trống hoặc chưa có nội dung bài tập. Em hãy đặt bài làm vào khung hình và chụp lại nhé.',
        actionTitle: 'Chụp lại bài làm',
      };
    case 'AI_RUNTIME_ERROR':
      return {
        title: 'Hệ thống đang bận',
        subtitle: 'Hệ thống nhận diện đang bận hoặc gặp gián đoạn tạm thời. Em hãy thử lại sau nhé.',
        actionTitle: 'Thử lại sau',
      };
    default:
      return {
        title: 'Chưa đủ kết quả để kiểm tra bài',
        subtitle: 'MathVision chưa thể kết luận bài đúng hay sai. Em có thể chụp lại hoặc nhờ thầy cô xem giúp nhé.',
        actionTitle: 'Thử lại',
      };
  }
}

export default function ReviewRequiredScreen() {
  const router = useRouter();
  const { reasonCode: initialReasonCode, submissionId } = useLocalSearchParams<{
    reasonCode?: string;
    submissionId?: string;
  }>();

  const [serverResult, setServerResult] = useState<SubmissionResult | null>(null);

  // Authoritative server fetch on mount
  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();
    if (submissionId) {
      getSubmissionService()
        .getSubmission(submissionId, undefined, controller.signal)
        .then((res) => {
          if (isMounted) {
            setServerResult(res);
            const target = resolveResultRoute(res);
            if (target.pathname !== '/results/review-required') router.replace(target as any);
          }
        })
        .catch(() => { /* Keep an unavailable result ungraded. */ });
    }
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [submissionId, router]);

  const effectiveReasonCode = serverResult?.reasonCode || initialReasonCode;
  const effectiveFlowDomain = serverResult?.flowDomain || 'ARITHMETIC';

  useEffect(() => {
    logFlowDomain('RESULT', effectiveFlowDomain);
  }, [effectiveFlowDomain]);

  const content = getReasonContent(effectiveReasonCode);

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <AppHeader title="Kiểm tra lại bài làm" showBack />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.spacerTop} />

        <StatusCard
          status="warning"
          title={content.title}
          subtitle={content.subtitle}
        />



        <View style={styles.spacer} />

        <View style={styles.actions}>
          <AppButton
            title={content.actionTitle}
            variant="primary"
            onPress={() => router.replace({ pathname: '/camera' as any, params: { mode: 'ARITHMETIC' } })}
          />
          <View style={{ height: SIZES.small }} />
          <AppButton
            title="Về trang chủ"
            variant="secondary"
            onPress={() => router.replace('/(tabs)')}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.large,
    flexGrow: 1,
    maxWidth: 500,
    width: '100%',
    alignSelf: 'center',
  },
  spacerTop: {
    height: SIZES.large,
  },
  spacer: {
    flex: 1,
    minHeight: SIZES.xlarge,
  },
  actions: {
    paddingBottom: SIZES.medium,
  },
});
