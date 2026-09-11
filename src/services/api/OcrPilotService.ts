import { Platform } from 'react-native';
import apiClient from './apiClient';
import { ensureFileUri } from '../image/imagePipeline';

export interface OcrTrialResult {
  trialId: string;
  status: string;
  recognizedText: string;
  predictedText?: string;
  verifiedTextRaw?: string;
  verdict: string;
  source: 'CAMERA' | 'GALLERY' | string;
  trainingEligible: boolean;
  modelName?: string;
  modelVersion?: string;
  createdAt?: string;
  feedbackAt?: string;
}

export interface OcrMetrics {
  totalTrials: number;
  verifiedTrials: number;
  correctCount: number;
  correctedCount: number;
  skippedCount: number;
  unverifiedCount: number;
  exactMatchRate: number;
  exactMatchPercentage: string;
}

export class OcrPilotService {
  static async createTrial(uri: string, source: 'CAMERA' | 'GALLERY' = 'CAMERA'): Promise<OcrTrialResult> {
    const cleanUri = ensureFileUri(Array.isArray(uri) ? uri[0] : uri);
    const formData = new FormData();

    const rawFilename = cleanUri.split('/').pop() || 'ocr_line.jpg';
    const safeFilename = rawFilename.includes('.') ? rawFilename.split('?')[0] : 'ocr_line.jpg';
    const match = /\.(\w+)$/.exec(safeFilename);
    const type = match && match[1].toLowerCase() === 'png' ? 'image/png' : 'image/jpeg';

    formData.append('image', {
      uri: Platform.OS === 'ios' ? cleanUri.replace('file://', '') : cleanUri,
      name: safeFilename,
      type,
    } as any);

    formData.append('source', source);

    const response = await apiClient.post<OcrTrialResult>('/ocr/trials', formData, {
      headers: {
        Accept: 'application/json',
      },
      transformRequest: [(data) => data],
    });

    return response.data;
  }

  static async getTrial(trialId: string): Promise<OcrTrialResult> {
    const response = await apiClient.get<OcrTrialResult>(`/ocr/trials/${trialId}`);
    return response.data;
  }

  static async submitFeedback(
    trialId: string,
    verdict: 'CORRECT' | 'CORRECTED' | 'SKIPPED',
    verifiedText?: string
  ): Promise<OcrTrialResult> {
    const response = await apiClient.post<OcrTrialResult>(`/ocr/trials/${trialId}/feedback`, {
      verdict,
      verifiedText,
    });
    return response.data;
  }

  static async getMetrics(): Promise<OcrMetrics> {
    const response = await apiClient.get<OcrMetrics>('/ocr/trials/metrics');
    return response.data;
  }
}
