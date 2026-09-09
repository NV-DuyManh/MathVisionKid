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
          bgcolor: '#DCFCE7',
          color: '#15803D',
          border: '1px solid #BBF7D0',
          fontWeight: 600,
          '& .MuiChip-icon': { color: '#15803D' },
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
        bgcolor: '#FEE2E2',
        color: '#B91C1C',
        border: '1px solid #FECACA',
        fontWeight: 600,
        '& .MuiChip-icon': { color: '#B91C1C' },
      }}
    />
  );
};
