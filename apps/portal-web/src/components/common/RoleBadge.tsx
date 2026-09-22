import React from 'react';
import { Chip } from '@mui/material';
import SchoolIcon from '@mui/icons-material/School';
import PersonIcon from '@mui/icons-material/Person';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';

interface RoleBadgeProps {
  role: string | null | undefined;
  size?: 'small' | 'medium';
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({ role, size = 'small' }) => {
  if (!role) return null;

  const normalized = role.toUpperCase().replace('ROLE_', '');

  if (normalized === 'STUDENT') {
    return (
      <Chip
        icon={<SchoolIcon fontSize="small" />}
        label="Học sinh"
        size={size}
        sx={{
          backgroundColor: '#EEF2FF',
          color: '#4F46E5',
          fontWeight: 600,
          border: '1px solid #C7D2FE',
          '& .MuiChip-icon': { color: '#4F46E5' },
        }}
      />
    );
  }

  if (normalized === 'TEACHER') {
    return (
      <Chip
        icon={<PersonIcon fontSize="small" />}
        label="Giáo viên"
        size={size}
        sx={{
          backgroundColor: '#ECFDF5',
          color: '#059669',
          fontWeight: 600,
          border: '1px solid #A7F3D0',
          '& .MuiChip-icon': { color: '#059669' },
        }}
      />
    );
  }

  if (normalized === 'ADMIN') {
    return (
      <Chip
        icon={<AdminPanelSettingsIcon fontSize="small" />}
        label="Quản trị viên"
        size={size}
        sx={{
          backgroundColor: '#FFFBEB',
          color: '#D97706',
          fontWeight: 600,
          border: '1px solid #FDE68A',
          '& .MuiChip-icon': { color: '#D97706' },
        }}
      />
    );
  }

  return (
    <Chip
      label={normalized}
      size={size}
      sx={{ fontWeight: 600 }}
    />
  );
};
