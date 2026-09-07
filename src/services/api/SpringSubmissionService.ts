import { Platform } from 'react-native';
import apiClient from './apiClient';
import { SubmissionService, SubmissionResult } from '../../types';

export class SpringSubmissionServiceClass implements SubmissionService {
  async uploadImage(uri: string): Promise<SubmissionResult> {
    const formData = new FormData();
    
    // Convert URI into a File/Blob equivalent for FormData
    const filename = uri.split('/').pop() || 'submission.jpg';
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1]}` : 'image/jpeg';
    
    // React Native uses any for FormData append with file objects
    formData.append('image', {
      uri: Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
      name: filename,
      type,
    } as any);
    
    // Optionally include source, assuming CAMERA as default for this integration
    formData.append('source', 'CAMERA');
    
    // Set explicit multipart header, though Axios usually handles it
    const response = await apiClient.post('/student/submissions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data as SubmissionResult;
  }

  async getSubmission(id: string, scenarioHint?: string): Promise<SubmissionResult> {
    const response = await apiClient.get(`/student/submissions/${id}`);
    return response.data as SubmissionResult;
  }

  async confirmToken(id: string, token: string): Promise<SubmissionResult> {
    const response = await apiClient.post(`/student/submissions/${id}/confirm-token`, {
      tokenId: 'manual-confirm', // Specific ID if needed by backend contract, or just value
      confirmedValue: token
    });
    return response.data as SubmissionResult;
  }

  async retrySubmission(id: string, uri: string): Promise<SubmissionResult> {
    const formData = new FormData();
    
    const filename = uri.split('/').pop() || 'retry.jpg';
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1]}` : 'image/jpeg';
    
    formData.append('image', {
      uri: Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
      name: filename,
      type,
    } as any);
    
    formData.append('source', 'CAMERA');

    const response = await apiClient.post(`/student/submissions/${id}/retry`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data as SubmissionResult;
  }
}

export const SpringSubmissionService = new SpringSubmissionServiceClass();
