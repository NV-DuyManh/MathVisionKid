import React from 'react';
import { Chip } from '@mui/material';
import { CheckCircleOutlined as CheckCircleOutlineIcon, Block as BlockIcon } from '@mui/icons-material';

interface StatusChipProps {
  active: boolean;
  size?: 'small' | 'medium';
}

export const StatusChip: React.FC<StatusChipProps> = ({ active, size = 'small' }) => {
  if (active) {
    return (
      <Chip
        icon={<CheckCircleOutlineIcon sx={{ fontSize: '14px !important' }} />}
        label="HOẠT ĐỘNG"
        size={size}
        sx={{
          height: 24,
          fontSize: '0.72rem',
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
  }

  return (
    <Chip
      icon={<BlockIcon sx={{ fontSize: '14px !important' }} />}
      label="VÔ HIỆU HÓA"
      size={size}
      sx={{
        height: 24,
        fontSize: '0.72rem',
        bgcolor: '#FEF2F2',
        color: '#DC2626',
        border: '1px solid #FECACA',
        fontWeight: 800,
        borderRadius: 1.5,
        letterSpacing: '0.02em',
        '& .MuiChip-icon': { color: '#DC2626' },
      }}
    />
  );
};
