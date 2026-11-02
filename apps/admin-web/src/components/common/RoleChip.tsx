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
            bgcolor: '#ECFDF5',
            color: '#059669',
            border: '1px solid #A7F3D0',
            fontWeight: 800,
            borderRadius: 1.5,
            letterSpacing: '0.02em',
            '& .MuiChip-icon': { color: '#059669' },
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
            bgcolor: '#EFF6FF',
            color: '#2563EB',
            border: '1px solid #BFDBFE',
            fontWeight: 800,
            borderRadius: 1.5,
            letterSpacing: '0.02em',
            '& .MuiChip-icon': { color: '#2563EB' },
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
            bgcolor: '#F1F5F9',
            color: '#0F172A',
            border: '1px solid #CBD5E1',
            fontWeight: 800,
            borderRadius: 1.5,
            letterSpacing: '0.02em',
            '& .MuiChip-icon': { color: '#0F172A' },
          }}
        />
      );
    default:
      return <Chip label={role} size={size} />;
  }
};
