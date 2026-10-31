import { Alert, Button } from '@mui/material';
export function errorMessage(error: unknown): string {
  const e = error as { response?: { status?: number }; code?: string };
  if (e?.code === 'ROLE_FORBIDDEN') return 'Tài khoản không có quyền quản trị hoặc đã bị khóa.';
  switch (e?.response?.status) {
    case 400: return 'Thông tin chưa hợp lệ. Kiểm tra các trường bắt buộc và điều kiện của tài khoản, lớp học.';
    case 401: return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
    case 403: return 'Bạn không có quyền thực hiện thao tác này.';
    case 404: return 'Không tìm thấy dữ liệu yêu cầu. Dữ liệu có thể đã thay đổi.';
    case 409: return 'Dữ liệu bị trùng hoặc đã thay đổi. Vui lòng kiểm tra và thử lại.';
    case 429: return 'Có quá nhiều yêu cầu. Vui lòng chờ một chút rồi thử lại.';
    default: return e?.response ? 'Máy chủ đang gặp sự cố. Vui lòng thử lại sau.' : 'Không thể kết nối máy chủ. Kiểm tra kết nối và thử lại.';
  }
}
export function RequestError({ error, retry }: { error: unknown; retry?: () => void }) {
  if (!error) return null;
  return <Alert severity="error" sx={{ mb: 2 }} action={retry && <Button color="inherit" onClick={retry}>Thử lại</Button>}>{errorMessage(error)}</Alert>;
}
