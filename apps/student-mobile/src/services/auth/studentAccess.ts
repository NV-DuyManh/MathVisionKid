export function requireStudent(profile: any) {
  if (profile?.role !== 'STUDENT' || profile.active !== true) {
    const message = profile?.role === 'ADMIN'
      ? 'Tài khoản quản trị cần sử dụng cổng quản trị trên trình duyệt. Vui lòng mở MathVision Kids và chọn không gian quản trị.'
      : profile?.role === 'TEACHER'
        ? 'Tài khoản giáo viên cần sử dụng cổng giáo viên trên trình duyệt.'
        : 'Tài khoản không có quyền truy cập hoặc đã bị khóa. Vui lòng đăng nhập lại.';
    throw Object.assign(new Error(message), { code: 'STUDENT_ACCESS_DENIED' });
  }
  return profile;
}
