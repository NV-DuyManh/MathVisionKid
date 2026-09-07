import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';
import { ImageQualityIssue } from '../../types';

export default function QualityFailureScreen() {
  const router = useRouter();
  const { issue, originalUri, submissionId } = useLocalSearchParams<{ issue: string, originalUri?: string, submissionId?: string }>();
  
  let title = 'Ảnh chưa được rõ';
  let subtitle = 'Hãy chụp lại ảnh thật rõ nét nhé.';
  let buttonTitle = 'Chụp lại';

  if (issue === ImageQualityIssue.BLUR) {
    title = 'Ảnh hơi mờ';
    subtitle = 'Giữ điện thoại yên rồi thử lại nhé.';
  } else if (issue === ImageQualityIssue.DARK) {
    title = 'Ảnh hơi tối';
    subtitle = 'Em hãy tìm chỗ sáng hơn để chụp nha.';
  } else if (issue === ImageQualityIssue.INCOMPLETE_CROP) {
    title = 'Chưa thấy hết bài';
    subtitle = 'Hãy đưa cả phép tính vào khung nhé.';
    buttonTitle = 'Chỉnh vùng bài';
  }

  return (
    <View style={styles.container}>
      <AppHeader title="Chụp ảnh" showBack />
      
      <View style={styles.content}>
        <View style={styles.spacer} />
        
        <StatusCard 
          status="warning" 
          title={title} 
          subtitle={subtitle}
        />

        <View style={styles.spacer} />

        <AppButton 
          title={buttonTitle} 
          onPress={() => {
            if (issue === ImageQualityIssue.INCOMPLETE_CROP) {
              router.replace({ 
                pathname: '/crop' as any,
                params: { uri: originalUri, retrySubmissionId: submissionId }
              });
            } else {
              router.replace({
                pathname: '/camera' as any,
                params: { retrySubmissionId: submissionId }
              });
            }
          }} 
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    padding: SIZES.medium,
  },
  spacer: {
    flex: 1,
  }
});
