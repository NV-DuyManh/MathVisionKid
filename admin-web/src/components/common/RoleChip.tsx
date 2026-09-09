import React from 'react';
import { Chip } from '@mui/material';
import SchoolIcon from '@mui/icons-material/School';
import PersonIcon from '@mui/icons-material/Person';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import type { Role } from '../../types';

interface RoleChipProps {
  role: Role;
  size?: 'small' | 'medium';
}

export const RoleChip: React.FC<RoleChipProps> = ({ role, size = 'small' }) => {
  switch (role) {
    case 'TEACHER':
      return (
        <Chip
          icon={<SchoolIcon sx={{ fontSize: '14px !important' }} />}
          label="GIÁO VIÊN"
          size={size}
          sx={{
            bgcolor: '#EFF6FF',
            color: '#1D4ED8',
            border: '1px solid #BFDBFE',
            fontWeight: 600,
            '& .MuiChip-icon': { color: '#1D4ED8' },
          }}
        />
      );
    case 'STUDENT':
      return (
        <Chip
          icon={<PersonIcon sx={{ fontSize: '14px !important' }} />}
          label="HỌC SINH"
          size={size}
          sx={{
            bgcolor: '#F0FDF4',
            color: '#166534',
            border: '1px solid #BBF7D0',
            fontWeight: 600,
            '& .MuiChip-icon': { color: '#166534' },
          }}
        />
      );
    case 'ADMIN':
      return (
        <Chip
          icon={<AdminPanelSettingsIcon sx={{ fontSize: '14px !important' }} />}
          label="QUẢN TRỊ VIÊN"
          size={size}
          sx={{
            bgcolor: '#F5F3FF',
            color: '#6D28D9',
            border: '1px solid #DDD6FE',
            fontWeight: 600,
            '& .MuiChip-icon': { color: '#6D28D9' },
          }}
        />
      );
    default:
      return <Chip label={role} size={size} />;
  }
};
