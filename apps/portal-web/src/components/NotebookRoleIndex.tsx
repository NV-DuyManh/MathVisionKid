import { Box, Typography } from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import SchoolOutlinedIcon from '@mui/icons-material/SchoolOutlined';
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined';
import AdminPanelSettingsOutlinedIcon from '@mui/icons-material/AdminPanelSettingsOutlined';
import { Link } from 'react-router-dom';
import { WEB_DESIGN } from '../../../../packages/ui-brand/src/web-design';

const spaces = [
  { title: 'Học sinh', description: 'Học toán từng bước và luyện tập.', path: '/student', icon: SchoolOutlinedIcon, role: 'student' },
  { title: 'Giáo viên', description: 'Quản lý lớp, giao bài và duyệt bài làm.', path: '/teacher-entry', icon: MenuBookOutlinedIcon, role: 'teacher' },
  { title: 'Quản trị viên', description: 'Quản lý tài khoản và lớp học.', path: '/admin-entry', icon: AdminPanelSettingsOutlinedIcon, role: 'admin' },
] as const;

export function NotebookRoleIndex() {
  return (
    <Box component="nav" aria-labelledby="notebook-index" sx={{ color: WEB_DESIGN.colors.ink, mb: 3 }}>
        <Typography id="notebook-index" component="h2" sx={{ fontWeight: 900, fontSize: WEB_DESIGN.typography.sizes.section, mb: 1 }}>
          Chọn không gian của bạn
        </Typography>
        <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0, borderBlockEnd: `1px solid ${WEB_DESIGN.colors.paperLine}` }}>
          {spaces.map(({ title, description, path, icon: Icon, role }) => (
            <Box component="li" key={path} sx={{ borderBlockStart: `1px solid ${WEB_DESIGN.colors.paperLine}` }}>
              <Box component={Link} to={path} sx={{
                display: 'grid', gridTemplateColumns: '40px minmax(0, 1fr) 20px', gap: 1.5, alignItems: 'center',
                minHeight: 64, px: 1, py: 1, color: 'inherit', textDecoration: 'none',
                '&:hover': { bgcolor: WEB_DESIGN.roles[role].tint },
                '&:focus-visible': { outline: `${WEB_DESIGN.focus.width}px solid ${WEB_DESIGN.focus.color}`, outlineOffset: -3 },
              }}>
                <Box sx={{ display: 'grid', placeItems: 'center', width: 40, height: 40,
                  borderRadius: '12px', bgcolor: WEB_DESIGN.roles[role].tint, color: WEB_DESIGN.roles[role].action }}>
                  <Icon aria-hidden="true" fontSize="small" />
                </Box>
                <Box component="span">
                  <Typography component="span" sx={{ display: 'block', fontWeight: 800 }}>{title}</Typography>
                  <Typography component="span" sx={{ display: 'block', fontSize: 14, color: '#334155' }}>{description}</Typography>
                </Box>
                <ArrowForwardIcon aria-hidden="true" sx={{ fontSize: 20 }} />
              </Box>
            </Box>
          ))}
        </Box>
    </Box>
  );
}
