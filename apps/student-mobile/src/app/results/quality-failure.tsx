import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SIZES } from '../../constants/theme';
import { StudentResultShell } from '../../components/ui/StudentResultShell';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';
import { ImageQualityIssue } from '../../types';

export default function QualityFailureScreen() {
  const router = useRouter();
  const { issue, originalUri, submissionId } = useLocalSearchParams<{
    issue: string;
    originalUri?: string;
    submissionId?: string;
  }>();

  let title = 'Ảnh bài tập chưa rõ nét';
  let subtitle = 'Em hãy chụp lại thật rõ để MathVision đọc chính xác từng chữ số nhé.';
  let buttonTitle = 'Chụp lại ảnh khác';

  if (issue === ImageQualityIssue.BLUR) {
    title = 'Ảnh bị rung hoặc hơi mờ';
    subtitle = 'Em hãy giữ điện thoại thật yên tay rồi chụp lại nhé.';
    buttonTitle = 'Chụp lại thật rõ';
  } else if (issue === ImageQualityIssue.DARK) {
    title = 'Ảnh hơi tối hoặc thiếu sáng';
    subtitle = 'Em hãy bật đèn hoặc di chuyển đến nơi sáng hơn để chụp nhé.';
    buttonTitle = 'Tìm chỗ sáng và chụp lại';
  } else if (issue === ImageQualityIssue.INCOMPLETE_CROP) {
    title = 'Chưa thấy trọn vẹn phép tính';
    subtitle = 'Phép tính bị mất một phần chữ số. Em hãy chỉnh lại khung hoặc chụp lại nhé.';
    buttonTitle = 'Chỉnh lại vùng bài';
  }

  return (
    <StudentResultShell title="Chất lượng ảnh">

        <StatusCard status="warning" title={title} subtitle={subtitle} />

        <View style={styles.actions}>
          <AppButton
            title={buttonTitle}
            variant="primary"
            onPress={() => {
              if (issue === ImageQualityIssue.INCOMPLETE_CROP && originalUri) {
                router.replace({
                  pathname: '/crop' as any,
                  params: { uri: originalUri, retrySubmissionId: submissionId },
                });
              } else {
                router.replace({
                  pathname: '/camera' as any,
                  params: { retrySubmissionId: submissionId, mode: 'ARITHMETIC' },
                });
              }
            }}
          />
          <View style={{ height: SIZES.small }} />
          <AppButton
            title="Về trang chủ"
            variant="secondary"
            onPress={() => router.replace('/(tabs)')}
          />
        </View>
      </StudentResultShell>
  );
}

const styles = StyleSheet.create({
  actions: {
    paddingBottom: SIZES.medium,
  },
});
