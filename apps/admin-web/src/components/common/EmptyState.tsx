import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import InboxOutlinedIcon from '@mui/icons-material/InboxOutlined';

export interface EmptyStateProps {
  title: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionText,
  onAction,
  icon = <InboxOutlinedIcon sx={{ fontSize: 42, color: '#94A3B8' }} />,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: { xs: 6, sm: 8 },
        px: 3,
        textAlign: 'center',
      }}
    >
      <Box
        sx={{
          width: 72,
          height: 72,
          borderRadius: '50%',
          bgcolor: '#F8FAFC',
          border: '1px solid #E2E8F0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 2.5,
        }}
      >
        {icon}
      </Box>
      <Typography
        variant="h6"
        sx={{
          color: '#0F172A',
          fontWeight: 800,
          fontSize: '1.1rem',
          mb: 0.75,
        }}
      >
        {title}
      </Typography>
      {description && (
        <Typography
          variant="body2"
          sx={{
            color: '#64748B',
            maxWidth: 420,
            mb: actionText ? 3 : 0,
            lineHeight: 1.55,
          }}
        >
          {description}
        </Typography>
      )}
      {actionText && onAction && (
        <Button
          variant="contained"
          onClick={onAction}
          sx={{
            borderRadius: 2.5,
            px: 3,
            py: 1,
            fontWeight: 800,
          }}
        >
          {actionText}
        </Button>
      )}
    </Box>
  );
};

export default EmptyState;
