export interface ApiErrorDetail {
  [key: string]: any;
}

export interface ApiError {
  code: string;
  message: string;
  requestId: string;
  details?: ApiErrorDetail;
}

export interface ApiErrorResponse {
  error: ApiError;
}
