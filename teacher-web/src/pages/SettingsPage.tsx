import { Box, Typography } from '@mui/material';

export default function SettingsPage() {
  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 4 }}>Cài đặt</Typography>
      <Typography color="text.secondary">Các tuỳ chọn cấu hình sẽ nằm ở đây.</Typography>
    </Box>
  );
}
