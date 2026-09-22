import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import InboxOutlinedIcon from '@mui/icons-material/InboxOutlined';

interface EmptyStateProps {
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
  icon = <InboxOutlinedIcon sx={{ fontSize: 48, color: '#94A3B8' }} />,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 8,
        px: 2,
        textAlign: 'center',
      }}
    >
      <Box sx={{ mb: 2 }}>{icon}</Box>
      <Typography variant="h6" gutterBottom sx={{ color: '#334155', fontWeight: 600 }}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" sx={{ color: '#64748B', maxWidth: 400, mb: 3 }}>
          {description}
        </Typography>
      )}
      {actionText && onAction && (
        <Button variant="contained" color="secondary" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </Box>
  );
};
