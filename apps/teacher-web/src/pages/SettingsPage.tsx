import { Box, Card, Divider, Typography } from '@mui/material';
import PersonOutlined from '@mui/icons-material/PersonOutlined';
import ShieldOutlined from '@mui/icons-material/ShieldOutlined';
import { useAuth } from '../components/layout/AuthContext';
import { PageHeader } from '../components/common/PageHeader';

const privacyPractices = [
  { title: 'Che thông tin trên ảnh', detail: 'Kiểm tra ảnh và che tên, lớp hoặc thông tin nhận diện trước khi tải bài làm lên.' },
  { title: 'Xem bài trong lớp được phân công', detail: 'Danh sách học sinh và bài làm được mở từ lớp mà tài khoản đang phụ trách.' },
  { title: 'Chốt điểm sau khi xem bài', detail: 'Đối chiếu ảnh với đề xuất điểm. Giáo viên xác nhận điểm chính thức.' },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.name || 'Giáo viên');
  const profile = [
    ['Họ và tên', displayName],
    ['Email công vụ', user?.email || '—'],
    ['Vai trò', 'Giáo viên'],
  ];

  return (
    <Box sx={{ maxWidth: 960 }}>
      <PageHeader title="Cài đặt & Thông tin tài khoản" subtitle="Xem hồ sơ giáo viên và hướng dẫn bảo vệ bài làm học sinh." />
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'minmax(0, 1fr)', lg: 'minmax(0, 2fr) minmax(0, 3fr)' },
        gap: 2, alignItems: 'start' }}>
        <Card component="section" aria-labelledby="teacher-profile-title" variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <PersonOutlined color="primary" aria-hidden="true" />
            <Typography id="teacher-profile-title" component="h2" variant="h6">Hồ sơ giáo viên</Typography>
          </Box>
          <Box component="dl" sx={{ m: 0 }}>
            {profile.map(([label, value]) => (
              <Box key={label} sx={{ py: 1.25, '& + &': { borderTop: '1px solid', borderColor: 'divider' } }}>
                <Typography component="dt" variant="body2" color="text.secondary">{label}</Typography>
                <Typography component="dd" sx={{ m: 0, fontWeight: 700, overflowWrap: 'anywhere' }}>{value}</Typography>
              </Box>
            ))}
          </Box>
        </Card>
        <Card component="section" aria-labelledby="teacher-privacy-title" variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ShieldOutlined color="primary" aria-hidden="true" />
            <Typography id="teacher-privacy-title" component="h2" variant="h6">Bảo vệ bài làm</Typography>
          </Box>
          <Divider />
          <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
            {privacyPractices.map(({ title, detail }) => (
              <Box component="li" key={title} sx={{ py: 1.5, '& + &': { borderTop: '1px solid', borderColor: 'divider' } }}>
                <Typography component="h3" variant="subtitle1" sx={{ fontWeight: 700 }}>{title}</Typography>
                <Typography variant="body2" color="text.secondary">{detail}</Typography>
              </Box>
            ))}
          </Box>
        </Card>
      </Box>
    </Box>
  );
}
