import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Image, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '../constants/theme';
import { MockSubmissionService } from '../services/api/MockSubmissionService';
import { SubmissionStatus } from '../types';

export default function ProcessingScreen() {
  const router = useRouter();
  const { uri } = useLocalSearchParams<{ uri: string }>();
  const [step, setStep] = useState(0); // 0: Đọc bài, 1: Kiểm tra, 2: Gợi ý

  useEffect(() => {
    let active = true;
    let submissionId = '';

    const runProcess = async () => {
      try {
        setStep(0);
        const result = await MockSubmissionService.uploadImage(uri as string);
        if (!active) return;
        submissionId = result.id;

        if (result.status === SubmissionStatus.NEEDS_RETAKE || result.status === SubmissionStatus.CROP_REQUIRED) {
          router.replace({ pathname: '/results/quality-failure', params: { issue: result.imageQualityIssue } });
          return;
        }
        if (result.status === SubmissionStatus.OUT_OF_SCOPE) {
          router.replace('/results/out-of-scope');
          return;
        }
        if (result.status === SubmissionStatus.REVIEW_REQUIRED) {
          router.replace('/results/review-required');
          return;
        }

        setStep(1);
        
        let scenarioHint = 'mock-correct';
        if (uri?.includes('mock-earliest-error')) scenarioHint = 'mock-earliest-error';
        if (uri?.includes('mock-confirm')) scenarioHint = 'mock-confirm';

        const polled = await MockSubmissionService.getSubmission(submissionId, scenarioHint);
        if (!active) return;

        if (polled.status === SubmissionStatus.NEEDS_CONFIRMATION) {
          router.replace({ 
            pathname: '/results/token-confirmation', 
            params: { 
              id: submissionId, 
              token: polled.ambiguousToken?.value || '' 
            } 
          });
          return;
        }

        setStep(2);
        await new Promise(r => setTimeout(r, 800));
        if (!active) return;
        
        if (polled.validation?.decision === 'VALID') {
          router.replace({
            pathname: '/results/correct',
            params: { data: JSON.stringify(polled) }
          });
        } else {
          router.replace({
            pathname: '/results/error-hint',
            params: { data: JSON.stringify(polled) }
          });
        }

      } catch (error) {
        console.error(error);
        if (active) router.back();
      }
    };

    runProcess();

    return () => { active = false; };
  }, [uri, router]);

  const stages = ['Đọc bài', 'Kiểm tra', 'Gợi ý'];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>MathVision đang xem bài...</Text>
      
      <View style={styles.imagePreview}>
        <Image source={{ uri: uri as string }} style={styles.image} resizeMode="contain" />
        <View style={styles.overlay}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </View>

      <View style={styles.progressContainer}>
        {/* Simple custom stepper */}
        <View style={styles.line} />
        <View style={styles.stepRow}>
          {stages.map((stage, index) => {
            const isCompleted = step > index;
            const isActive = step === index;
            return (
              <View key={stage} style={styles.stepWrapper}>
                <View style={[
                  styles.dot, 
                  isActive && styles.dotActive,
                  isCompleted && styles.dotCompleted
                ]} />
                <Text style={[
                  styles.stepText,
                  isActive && styles.stepTextActive
                ]}>{stage}</Text>
              </View>
            );
          })}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    padding: SIZES.large,
    paddingTop: 120,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: SIZES.xxlarge,
  },
  imagePreview: {
    width: 220,
    height: 220,
    borderRadius: SIZES.cardRadius,
    overflow: 'hidden',
    marginBottom: SIZES.xxlarge,
    backgroundColor: '#000',
  },
  image: {
    flex: 1,
  },
  overlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(255,255,255,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressContainer: {
    width: '100%',
    paddingHorizontal: SIZES.large,
    position: 'relative',
  },
  line: {
    position: 'absolute',
    top: 8,
    left: SIZES.xxlarge,
    right: SIZES.xxlarge,
    height: 2,
    backgroundColor: COLORS.border,
    zIndex: 0,
  },
  stepRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    zIndex: 1,
  },
  stepWrapper: {
    alignItems: 'center',
  },
  dot: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: COLORS.surface,
    borderWidth: 2,
    borderColor: COLORS.border,
    marginBottom: 8,
  },
  dotActive: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary,
  },
  dotCompleted: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary,
  },
  stepText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    fontWeight: '500',
  },
  stepTextActive: {
    color: COLORS.primaryDark,
    fontWeight: '700',
  }
});
