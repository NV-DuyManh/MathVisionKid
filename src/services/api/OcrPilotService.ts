import { Platform } from 'react-native';
import apiClient from './apiClient';
import { ensureFileUri } from '../image/imagePipeline';

export interface OcrTrialResult {
  trialId: string;
  status: string;
  recognizedText: string;
  predictedText?: string;
  verifiedTextRaw?: string;
  verifiedTextNormalized?: string;
  verdict: string;
  source: 'CAMERA' | 'GALLERY' | string;
  domain?: string;
  trainingEligible: boolean;
  privacyConfirmed?: boolean;
  isTestData?: boolean;
  confidence?: number | null;
  modelName?: string;
  modelVersion?: string;
  checkpointSha256?: string;
  vocabSha256?: string;
  preprocessingVersion?: string;
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
  exactMatchRate: number | null;
  exactMatchPercentage: string;
  characterErrorRate?: number | null;
  cerPercentage?: string;
  domain?: string;
  evaluationScope?: string;
}

export interface LineBox {
  line_id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  order: number;
}

export interface MultilineDetectResult {
  width: number;
  height: number;
  lines: LineBox[];
}

export interface MultilineLineResult {
  lineId: string;
  lineOrder: number;
  x: number;
  y: number;
  width: number;
  height: number;
  lineImageObjectKey: string;
  lineImageSha256: string;
  predictedText: string;
  verifiedTextRaw?: string;
  verifiedTextNormalized?: string;
  verdict: string;
  trainingEligible: boolean;
  feedbackAt?: string;
}

export interface MultilineTrialResult {
  trialId: string;
  userId?: string;
  source: string;
  pageImageObjectKey: string;
  pageImageSha256: string;
  pageWidth: number;
  pageHeight: number;
  privacyConfirmed: boolean;
  isTestData: boolean;
  dataOrigin: string;
  status: string;
  createdAt: string;
  lines: MultilineLineResult[];
}

export class OcrPilotService {
  // Single-line Pilot 1 methods
  static async createTrial(
    uri: string, 
    source: 'CAMERA' | 'GALLERY' = 'CAMERA',
    isTestData: boolean = false,
    privacyConfirmed: boolean = true
  ): Promise<OcrTrialResult> {
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
    formData.append('isTestData', String(isTestData));
    formData.append('privacyConfirmed', String(privacyConfirmed));

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
    verifiedText?: string,
    isTestData?: boolean
  ): Promise<OcrTrialResult> {
    const response = await apiClient.post<OcrTrialResult>(`/ocr/trials/${trialId}/feedback`, {
      verdict,
      verifiedText,
      isTestData,
    });
    return response.data;
  }

  static async getMetrics(): Promise<OcrMetrics> {
    const response = await apiClient.get<OcrMetrics>('/ocr/trials/metrics');
    return response.data;
  }

  // Multi-line Pilot 2 methods
  static async detectLines(
    uri: string,
    privacyConfirmed: boolean = true
  ): Promise<MultilineDetectResult> {
    const cleanUri = ensureFileUri(Array.isArray(uri) ? uri[0] : uri);
    const formData = new FormData();

    const rawFilename = cleanUri.split('/').pop() || 'page.jpg';
    const safeFilename = rawFilename.includes('.') ? rawFilename.split('?')[0] : 'page.jpg';
    const match = /\.(\w+)$/.exec(safeFilename);
    const type = match && match[1].toLowerCase() === 'png' ? 'image/png' : 'image/jpeg';

    formData.append('image', {
      uri: Platform.OS === 'ios' ? cleanUri.replace('file://', '') : cleanUri,
      name: safeFilename,
      type,
    } as any);

    formData.append('privacyConfirmed', String(privacyConfirmed));

    const response = await apiClient.post<MultilineDetectResult>('/ocr/multiline/detect', formData, {
      headers: {
        Accept: 'application/json',
      },
      transformRequest: [(data) => data],
    });

    return response.data;
  }

  static async createMultilineTrial(
    uri: string,
    confirmedLines: LineBox[],
    source: 'CAMERA' | 'GALLERY' = 'CAMERA',
    privacyConfirmed: boolean = true
  ): Promise<MultilineTrialResult> {
    const cleanUri = ensureFileUri(Array.isArray(uri) ? uri[0] : uri);
    const formData = new FormData();

    const rawFilename = cleanUri.split('/').pop() || 'page.jpg';
    const safeFilename = rawFilename.includes('.') ? rawFilename.split('?')[0] : 'page.jpg';
    const match = /\.(\w+)$/.exec(safeFilename);
    const type = match && match[1].toLowerCase() === 'png' ? 'image/png' : 'image/jpeg';

    formData.append('image', {
      uri: Platform.OS === 'ios' ? cleanUri.replace('file://', '') : cleanUri,
      name: safeFilename,
      type,
    } as any);

    formData.append('source', source);
    formData.append('privacyConfirmed', String(privacyConfirmed));
    formData.append('confirmedLines', JSON.stringify(confirmedLines));

    const response = await apiClient.post<MultilineTrialResult>('/ocr/multiline/trials', formData, {
      headers: {
        Accept: 'application/json',
      },
      transformRequest: [(data) => data],
    });

    return response.data;
  }

  static async getMultilineTrial(trialId: string): Promise<MultilineTrialResult> {
    const response = await apiClient.get<MultilineTrialResult>(`/ocr/multiline/trials/${trialId}`);
    return response.data;
  }

  static async submitLineFeedback(
    trialId: string,
    lineId: string,
    verdict: 'CORRECT' | 'CORRECTED' | 'SKIPPED',
    verifiedText?: string
  ): Promise<MultilineLineResult> {
    const response = await apiClient.post<MultilineLineResult>(
      `/ocr/multiline/trials/${trialId}/lines/${lineId}/feedback`,
      {
        verdict,
        verifiedText,
      }
    );
    return response.data;
  }
}

