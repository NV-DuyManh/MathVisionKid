import { isAxiosError } from 'axios';
import apiClient from '../../services/api/apiClient';

const GRANT_HEADER = 'X-MathVision-Parent-Grant';
const CONTROL = '/student/parent-control';
export type ParentControlStatus = { pinConfigured: boolean; dailyLimitReached: boolean; activityVerified: boolean };
export type ParentSettings = { dailyMinutes: number | null; gameMinutes?: number | null; grant?: string };

export async function readParentControlStatus(signal?: AbortSignal) {
  return (await apiClient.get<ParentControlStatus>(CONTROL + '/status', { signal, timeout: 5000 })).data;
}

export async function openParentMode(pin: string, setup: boolean, signal?: AbortSignal) {
  const { data, headers } = await apiClient.post<ParentSettings>(CONTROL + (setup ? '/pin' : '/unlock'), { pin }, { signal });
  const grant = headers[GRANT_HEADER.toLowerCase()];
  return typeof grant === 'string' ? { ...data, grant } : data;
}

export async function readParentSettings(grant: string, signal: AbortSignal) {
  return (await apiClient.get<ParentSettings>(CONTROL + '/settings', {
    headers: { [GRANT_HEADER]: grant }, signal, timeout: 5000,
  })).data;
}

export function isParentGrantRejected(cause: unknown) {
  const code = isAxiosError(cause) && cause.response?.data?.error?.code;
  return code === 'PARENT_GRANT_REQUIRED' || code === 'PARENT_PIN_REQUIRED';
}

export type ParentPinPurpose = 'SETUP' | 'RESET';

export async function requestParentPinCode(purpose: ParentPinPurpose, signal: AbortSignal) {
  return (await apiClient.post<{ maskedEmail: string }>(CONTROL + '/pin-code/request', { purpose }, { signal })).data;
}

export async function confirmParentPinCode(purpose: ParentPinPurpose, code: string, pin: string, signal: AbortSignal) {
  await apiClient.post(CONTROL + '/pin-code/confirm', { purpose, code, pin }, { signal });
}

export async function saveParentDailyLimit(pin: string, minutes: number | null, signal?: AbortSignal) {
  return (await apiClient.put<ParentSettings>(CONTROL + '/daily-limit', { pin, minutes }, { signal })).data;
}

export async function saveParentGameLimit(pin: string, minutes: number | null, signal?: AbortSignal) {
  return (await apiClient.put<ParentSettings>(CONTROL + '/game-limit', { pin, minutes }, { signal })).data;
}

export function parentControlError(cause: unknown) {
  const code = isAxiosError(cause) ? cause.response?.data?.error?.code : undefined;
  if (code === 'PARENT_PIN_INVALID') return 'Mã PIN chưa đúng. Vui lòng thử lại.';
  if (code === 'PARENT_PIN_LOCKED') return 'Đã nhập sai nhiều lần. Vui lòng thử lại sau 5 phút.';
  if (code === 'PARENT_PIN_CODE_INVALID') return 'Mã xác nhận chưa đúng hoặc đã hết hạn.';
  if (code === 'PARENT_PIN_CODE_ATTEMPTS') return 'Bạn đã nhập sai nhiều lần. Vui lòng yêu cầu mã mới.';
  if (code === 'PARENT_PIN_CODE_RATE_LIMIT') return 'Bạn đã yêu cầu mã gần đây. Vui lòng chờ rồi thử lại.';
  if (code === 'PARENT_PIN_STATE_CHANGED') return 'Trạng thái PIN đã thay đổi. Hãy mở lại Góc phụ huynh.';
  if (code === 'EMAIL_NOT_CONFIGURED' || code === 'PARENT_PIN_EMAIL_UNAVAILABLE') return 'Chưa gửi được email xác nhận. Vui lòng thử lại sau.';
  if (code === 'PARENT_PIN_EXISTS') return 'Mã PIN đã được thiết lập. Nhập mã hiện tại để tiếp tục.';
  return 'Chưa kết nối được với tài khoản. Vui lòng thử lại.';
}
