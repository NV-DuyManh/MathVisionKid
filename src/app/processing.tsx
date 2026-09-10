import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Image, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES, SHADOWS } from '../constants/theme';
import { getSubmissionService } from '../services/api/SubmissionServiceFactory';
import { SubmissionStatus } from '../types';
import { Ionicons } from '@expo/vector-icons';

export default function ProcessingScreen() {
  const router = useRouter();
  const { uri, originalUri, retrySubmissionId } = useLocalSearchParams<{
    uri: string;
    originalUri?: string;
    retrySubmissionId?: string;
  }>();
  const [step, setStep] = useState(0); // 0: Đọc bài, 1: Kiểm tra, 2: Gợi ý

  useEffect(() => {
    let active = true;
    let submissionId = '';

    const runProcess = async () => {
      try {
        setStep(0);
        const submissionService = getSubmissionService();
        let result;
        if (retrySubmissionId) {
          result = await submissionService.retrySubmission(retrySubmissionId, uri as string);
        } else {
          result = await submissionService.uploadImage(uri as string);
        }
        if (!active) return;
        submissionId = result.id;

        if (
          result.status === SubmissionStatus.NEEDS_RETAKE ||
          result.status === SubmissionStatus.CROP_REQUIRED
        ) {
          router.replace({
            pathname: '/results/quality-failure' as any,
            params: {
              issue: result.imageQualityIssue,
              originalUri,
              submissionId,
            },
          });
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
        if (result.status === SubmissionStatus.FEEDBACK_READY) {
          router.replace({ pathname: '/results/correct', params: { data: JSON.stringify(result) } });
          return;
        }

        setStep(1);

        let scenarioHint = 'mock-correct';
        if (uri?.includes('mock-earliest-error')) scenarioHint = 'mock-earliest-error';
        if (uri?.includes('mock-confirm')) scenarioHint = 'mock-confirm';

        // Polling loop
        let polled = result;
        while (active && polled.status === SubmissionStatus.PROCESSING) {
          await new Promise(r => setTimeout(r, 2000));
          if (!active) return;
          try {
            polled = await submissionService.getSubmission(submissionId, scenarioHint);
          } catch (e) {
            console.error('Polling error', e);
          }
        }

        if (!active) return;

        if (polled.status === SubmissionStatus.NEEDS_CONFIRMATION) {
          router.replace({
            pathname: '/results/token-confirmation',
            params: {
              id: submissionId,
              token: polled.ambiguousToken?.value || '',
            },
          });
          return;
        }

        if (
          polled.status === SubmissionStatus.NEEDS_RETAKE ||
          polled.status === SubmissionStatus.CROP_REQUIRED
        ) {
          router.replace({
            pathname: '/results/quality-failure' as any,
            params: {
              issue: polled.imageQualityIssue,
              originalUri,
              submissionId,
            },
          });
          return;
        }

        if (polled.status === SubmissionStatus.OUT_OF_SCOPE) {
          router.replace('/results/out-of-scope');
          return;
        }

        if (polled.status === SubmissionStatus.REVIEW_REQUIRED) {
          router.replace('/results/review-required');
          return;
        }

        setStep(2);
        await new Promise(r => setTimeout(r, 800));
        if (!active) return;

        if (polled.validation?.decision === 'VALID') {
          router.replace({
            pathname: '/results/correct',
            params: { data: JSON.stringify(polled) },
          });
        } else {
          router.replace({
            pathname: '/results/error-hint',
            params: { data: JSON.stringify(polled) },
          });
        }
      } catch (error) {
        console.error('Processing error', error);
        if (active) router.back();
      }
    };

    runProcess();

    return () => {
      active = false;
    };
  }, [uri, router, originalUri, retrySubmissionId]);

  const stages = [
    { label: 'Đọc bài', desc: 'Nhận diện chữ số' },
    { label: 'Kiểm tra', desc: 'So sánh từng hàng' },
    { label: 'Gợi ý', desc: 'Chuẩn bị kết quả' },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>MathVision đang xem bài...</Text>
        <Text style={styles.subtitle}>Em chờ một lát để trợ lý kiểm tra từng chữ số nhé.</Text>

        <View style={[styles.imagePreview, SHADOWS.small]}>
          <Image source={{ uri: uri as string }} style={styles.image} resizeMode="contain" />
          <View style={styles.overlay}>
            <ActivityIndicator size="large" color={COLORS.primary} />
          </View>
        </View>

        {/* Stepper progress indicator */}
        <View style={styles.progressContainer}>
          <View style={styles.stepRow}>
            {stages.map((stage, index) => {
              const isCompleted = step > index;
              const isActive = step === index;
              return (
                <View key={stage.label} style={styles.stepWrapper}>
                  <View
                    style={[
                      styles.dot,
                      isActive && styles.dotActive,
                      isCompleted && styles.dotCompleted,
                    ]}
                  >
                    {isCompleted ? (
                      <Ionicons name="checkmark" size={14} color="#FFFFFF" />
                    ) : (
                      <Text
                        style={[
                          styles.dotNumber,
                          isActive && styles.dotNumberActive,
                        ]}
                      >
                        {index + 1}
                      </Text>
                    )}
                  </View>
                  <Text
                    style={[
                      styles.stepText,
                      isActive && styles.stepTextActive,
                      isCompleted && styles.stepTextCompleted,
                    ]}
                  >
                    {stage.label}
                  </Text>
                  <Text style={styles.stepDesc}>{stage.desc}</Text>
                </View>
              );
            })}
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SIZES.large,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.cardRadius,
    padding: SIZES.xlarge,
    alignItems: 'center',
    width: '100%',
    maxWidth: 440,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 4,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: SIZES.xlarge,
    lineHeight: 20,
  },
  imagePreview: {
    width: 200,
    height: 200,
    borderRadius: SIZES.cardRadius,
    overflow: 'hidden',
    marginBottom: SIZES.xxlarge,
    backgroundColor: '#0F172A',
    position: 'relative',
  },
  image: {
    flex: 1,
  },
  overlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(255, 255, 255, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressContainer: {
    width: '100%',
    paddingTop: SIZES.small,
  },
  stepRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  stepWrapper: {
    alignItems: 'center',
    flex: 1,
  },
  dot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#F1F5F9',
    borderWidth: 2,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 6,
  },
  dotActive: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.surfaceSubdued,
  },
  dotCompleted: {
    borderColor: COLORS.success,
    backgroundColor: COLORS.success,
  },
  dotNumber: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textSecondary,
  },
  dotNumberActive: {
    color: COLORS.primaryDark,
  },
  stepText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  stepTextActive: {
    color: COLORS.primaryDark,
    fontWeight: '800',
  },
  stepTextCompleted: {
    color: COLORS.success,
    fontWeight: '700',
  },
  stepDesc: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
    textAlign: 'center',
  },
});
