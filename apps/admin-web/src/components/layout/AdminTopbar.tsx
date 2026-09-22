import React from 'react';
import { Box, AppBar, Toolbar, Typography, Chip } from '@mui/material';
import { useAuth } from '../../context/AuthContext';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';

interface AdminTopbarProps {
  title?: string;
  subtitle?: string;
}

export const AdminTopbar: React.FC<AdminTopbarProps> = ({ title, subtitle }) => {
  const { user } = useAuth();

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        bgcolor: '#FFFFFF',
        color: '#0F172A',
        borderBottom: '1px solid #E2E8F0',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, md: 4 } }}>
        <Box>
          {title && (
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A', lineHeight: 1.2 }}>
              {title}
            </Typography>
          )}
          {subtitle && (
            <Typography variant="caption" sx={{ color: '#64748B' }}>
              {subtitle}
            </Typography>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Chip
            icon={<AdminPanelSettingsIcon sx={{ fontSize: '14px !important' }} />}
            label="ADMIN"
            size="small"
            sx={{
              bgcolor: '#F1F5F9',
              color: '#0F172A',
              fontWeight: 700,
              border: '1px solid #CBD5E1',
            }}
          />
          <Typography variant="body2" sx={{ color: '#475569', fontWeight: 500, display: { xs: 'none', sm: 'block' } }}>
            {user?.email}
          </Typography>
        </Box>
      </Toolbar>
    </AppBar>
  );
};
