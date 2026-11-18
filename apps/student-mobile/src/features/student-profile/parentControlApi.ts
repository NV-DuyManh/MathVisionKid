import { isAxiosError } from 'axios';
import apiClient from '../../services/api/apiClient';

const CONTROL = '/student/parent-control';
export type ParentControlStatus = { pinConfigured: boolean; dailyLimitReached: boolean };
export type ParentSettings = { dailyMinutes: number | null };

export async function readParentControlStatus(signal?: AbortSignal) {
  return (await apiClient.get<ParentControlStatus>(CONTROL + '/status', { signal, timeout: 5000 })).data;
}

export async function openParentMode(pin: string, setup: boolean) {
  return (await apiClient.post<ParentSettings>(CONTROL + (setup ? '/pin' : '/unlock'), { pin })).data;
}

export async function saveParentDailyLimit(pin: string, minutes: number | null) {
  return (await apiClient.put<ParentSettings>(CONTROL + '/daily-limit', { pin, minutes })).data;
}

export function parentControlError(cause: unknown) {
  const code = isAxiosError(cause) ? cause.response?.data?.error?.code : undefined;
  if (code === 'PARENT_PIN_INVALID') return 'Mã PIN chưa đúng. Vui lòng thử lại.';
  if (code === 'PARENT_PIN_LOCKED') return 'Đã nhập sai nhiều lần. Vui lòng thử lại sau 5 phút.';
  if (code === 'PARENT_PIN_EXISTS') return 'Mã PIN đã được thiết lập. Nhập mã hiện tại để tiếp tục.';
  return 'Chưa kết nối được với tài khoản. Vui lòng thử lại.';
}
