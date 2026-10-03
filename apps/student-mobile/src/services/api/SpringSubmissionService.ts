import { Platform } from 'react-native';
import apiClient from './apiClient';
import { SubmissionService, SubmissionResult, TokenCorrection } from '../../types';
import { ensureFileUri } from '../../features/recognition/image/imagePipeline';
import { recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';

function normalizeResult(data: any, fallbackId?: string): SubmissionResult {
  const id = data?.submissionId || data?.id || fallbackId;
  if (!id || !data?.status) throw new Error('Submission response is incomplete');
  return { ...data, id };
}

async function imageForm(uri: string, signal?: AbortSignal): Promise<FormData> {
  const cleanUri = ensureFileUri(uri);
  const filename = cleanUri.split('/').pop()?.split('?')[0];
  const name = filename && /\.(jpe?g|png)$/i.test(filename) ? filename : 'submission.jpg';
  const type = /\.png$/i.test(name) ? 'image/png' : 'image/jpeg';
  const form = new FormData();
  if (Platform.OS === 'web') {
    const response = await fetch(cleanUri, { signal });
    if (!response.ok) throw new Error('Could not read the selected photo');
    form.append('image', await response.blob(), name);
  } else {
    form.append('image', { uri: Platform.OS === 'ios' ? cleanUri.replace('file://', '') : cleanUri, name, type } as any);
  }
  form.append('source', recognitionDraftStore.getDraft()?.source || 'CAMERA');
  return form;
}

export class SpringSubmissionServiceClass implements SubmissionService {
  async uploadImage(uri: string, signal?: AbortSignal): Promise<SubmissionResult> {
    const form = await imageForm(uri, signal);
    const response = await apiClient.post('/student/submissions', form, {
      signal, headers: { Accept: 'application/json' }, transformRequest: [(data) => data],
    });
    return normalizeResult(response.data);
  }

  async getSubmission(id: string, _scenarioHint?: string, signal?: AbortSignal): Promise<SubmissionResult> {
    const response = await apiClient.get(`/student/submissions/${encodeURIComponent(id)}`, { signal });
    return normalizeResult(response.data, id);
  }

  async confirmToken(id: string, correction: TokenCorrection, signal?: AbortSignal): Promise<SubmissionResult> {
    const response = await apiClient.post(`/student/submissions/${encodeURIComponent(id)}/confirm-token`, correction, { signal });
    return normalizeResult(response.data, id);
  }

  async retrySubmission(id: string, uri: string, signal?: AbortSignal): Promise<SubmissionResult> {
    const form = await imageForm(uri, signal);
    const response = await apiClient.post(`/student/submissions/${encodeURIComponent(id)}/retry`, form, {
      signal, headers: { Accept: 'application/json' }, transformRequest: [(data) => data],
    });
    return normalizeResult(response.data, id);
  }
}

export const SpringSubmissionService = new SpringSubmissionServiceClass();
