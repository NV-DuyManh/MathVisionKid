import { Platform } from 'react-native';
import apiClient from './apiClient';
import { ensureFileUri } from '../image/imagePipeline';

/**
 * Send a multipart POST request with file + string params.
 *
 * IMPORTANT — Two independent bugs must be avoided:
 *
 * 1. Expo SDK 57 overrides global.fetch with its own "winter/fetch" which
 *    converts FormData via convertFormDataAsync(). That code only handles
 *    string | Blob | {bytes()}. React Native's FormData file objects
 *    ({uri, name, type}) are NONE of those → throws
 *    "Unsupported FormDataPart implementation".
 *    FIX: Use XMLHttpRequest — it bypasses Expo's fetch and goes directly
 *    to React Native's native OkHttp networking layer.
 *
 * 2. On Android, OkHttp can struggle with mixed string + file FormData parts.
 *    FIX: Put string params in URL query string (Spring Boot @RequestParam
 *    reads from both), keep FormData file-only.
 */
async function postMultipart<T>(
  endpoint: string,
  fileField: { key: string; uri: string; name: string; type: string },
  stringParams: Record<string, string> = {},
  signal?: AbortSignal,
): Promise<T> {
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // Build query string from stringParams
  const qs = Object.entries(stringParams)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&');
  const url = qs ? `${path}?${qs}` : path;

  // FormData with ONLY the file part — no string parts
  const formData = new FormData();
  formData.append(fileField.key, {
    uri: fileField.uri,
    name: fileField.name,
    type: fileField.type,
  } as any);

  console.log('[MULTIPART_TRANSPORT]', {
    baseURL: apiClient.defaults.baseURL,
    endpoint: url,
    fullTarget: `${apiClient.defaults.baseURL || ''}${url}`,
    fileName: fileField.name,
    fileUri: fileField.uri,
    fileType: fileField.type,
    timestamp: new Date().toISOString()
  });

  // apiClient handles Authorization header and token refresh automatically
  // React Native's Axios adapter uses XMLHttpRequest natively and handles {uri,name,type}
  const response = await apiClient.post<T>(url, formData, {
    transformRequest: [(data) => data],
    signal,
  });
  return response.data;
}

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
}

export interface OcrMetrics {
  totalTrials: number;
  reviewedTrials: number;
  correctedTrials: number;
  verifiedTrials: number;
  skippedTrials: number;
  averageConfidence: number;
  accuracyRate: number;
}

export interface LineBox {
  line_id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  order: number;
  text?: string;
  rawOcrText?: string;
  rawOcrConfidence?: number;
  correctedText?: string;
  correctionConfidence?: number;
  correctionApplied?: boolean;
  correctionDecision?: string;
  finalText?: string;
  minTokenConfidence?: number;
  p10TokenConfidence?: number;
  meanTokenConfidence?: number;
  blankRatio?: number;
  meanEntropy?: number;
}

export interface MultilineDetectResult {
  width: number;
  height: number;
  lines: LineBox[];
  diagnostics?: Record<string, any>;
  requestId?: string;
}

export interface MultilineLineResult {
  lineId: string;
  lineOrder?: number;
  lineIndex?: number;
  boxX?: number;
  boxY?: number;
  boxWidth?: number;
  boxHeight?: number;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  lineImageObjectKey?: string;
  lineImageSha256?: string;
  predictedText: string;
  confidence?: number;
  rawOcrText?: string;
  rawOcrConfidence?: number;
  correctedText?: string;
  correctionConfidence?: number;
  correctionApplied?: boolean;
  correctionDecision?: string;
  finalText?: string;
  minTokenConfidence?: number;
  p10TokenConfidence?: number;
  meanTokenConfidence?: number;
  blankRatio?: number;
  meanEntropy?: number;
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
  canonicalMatched?: boolean;
  fixtureId?: string;
  recognitionSource?: string;
  recognitionEngine?: string;
  segmentationSource?: string;
  correctionSource?: string;
  finalTextSource?: string;
  requestId?: string;
  diagnostics?: Record<string, any>;
}

export class OcrPilotService {
  // Helper to extract file info from a URI
  private static fileInfoFromUri(rawUri: string, fallbackName: string) {
    const cleanUri = ensureFileUri(Array.isArray(rawUri) ? rawUri[0] : rawUri);
    const rawFilename = cleanUri.split('/').pop() || fallbackName;
    const safeFilename = rawFilename.includes('.') ? rawFilename.split('?')[0] : fallbackName;
    const match = /\.(\w+)$/.exec(safeFilename);
    const type = match && match[1].toLowerCase() === 'png' ? 'image/png' : 'image/jpeg';
    const uri = Platform.OS === 'ios' ? cleanUri.replace('file://', '') : cleanUri;
    return { uri, name: safeFilename, type };
  }

  // Single-line Pilot 1 methods
  static async createTrial(
    uri: string, 
    source: 'CAMERA' | 'GALLERY' = 'CAMERA',
    isTestData: boolean = false,
    privacyConfirmed: boolean = true
  ): Promise<OcrTrialResult> {
    const file = this.fileInfoFromUri(uri, 'ocr_line.jpg');
    return await postMultipart<OcrTrialResult>(
      '/ocr/trials',
      { key: 'image', ...file },
      {
        source,
        isTestData: String(isTestData),
        privacyConfirmed: String(privacyConfirmed),
      },
    );
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
    const file = this.fileInfoFromUri(uri, 'page.jpg');
    console.log('[OCR_PILOT] Requesting detectLines for URI:', uri, '| BaseURL:', apiClient.defaults.baseURL);
    try {
      const result = await postMultipart<MultilineDetectResult>(
        '/ocr/multiline/detect',
        { key: 'image', ...file },
        { 
          privacyConfirmed: String(privacyConfirmed),
          _t: Date.now().toString()
        },
      );
      console.log('[OCR_PILOT] detectLines success:', {
        width: result.width,
        height: result.height,
        linesCount: result.lines?.length || 0,
        detectorVersion: (result as any).detectorVersion || (result as any).detector_version,
      });
      if (__DEV__ && result.diagnostics) {
        const d = result.diagnostics;
        result.requestId = d.requestId || (result as any).requestId;
        console.log(
          `[OCR-PHYSICAL]\n` +
          `requestId=${result.requestId || 'unknown'}\n` +
          `recognitionEngine=${d.recognitionEngine || 'CRNN'}\n` +
          `segmentationSource=${d.segmentationSource || 'LOCAL_CV'}\n` +
          `correctionSource=${d.correctionSource || 'NONE'}\n` +
          `finalTextSource=${d.finalTextSource || 'CRNN_RAW'}\n` +
          `groqLineAssistUsed=${d.groqLineAssistUsed ?? false}\n` +
          `groqCorrectionUsed=${d.groqCorrectionUsed ?? false}\n` +
          `groqCalls=${d.groqCalls ?? 0}\n` +
          `lineCount=${result.lines?.length || 0}\n` +
          `totalLatencyMs=${d.totalLatencyMs ?? 'N/A'}`
        );
      }
      return result;
    } catch (err: any) {
      console.error('[OCR_PILOT] detectLines network/server error:', err?.message || err, err?.response?.data);
      throw err;
    }
  }

  static async createMultilineTrial(
    uri: string,
    confirmedLines: LineBox[],
    source: 'CAMERA' | 'GALLERY' = 'CAMERA',
    privacyConfirmed: boolean = true,
    signal?: AbortSignal
  ): Promise<MultilineTrialResult> {
    const file = this.fileInfoFromUri(uri, 'page.jpg');
    return await postMultipart<MultilineTrialResult>(
      '/ocr/multiline/trials',
      { key: 'image', ...file },
      {
        source,
        privacyConfirmed: String(privacyConfirmed),
        confirmedLines: JSON.stringify(confirmedLines),
      },
      signal
    );
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

