import React from 'react';
import { Box, Typography, Chip } from '@mui/material';

export interface PageHeaderProps {
  title: string;
  description?: string;
  subtitle?: string;
  badge?: string;
  actions?: React.ReactNode;
  action?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  subtitle,
  badge,
  actions,
  action,
}) => {
  const desc = description || subtitle;
  const acts = actions || action;

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: { xs: 'flex-start', sm: 'flex-end' },
        flexDirection: { xs: 'column', sm: 'row' },
        gap: 2,
        mb: 3,
      }}
    >
      <Box sx={{ minWidth: 0 }}>
        {badge && (
          <Chip
            label={badge}
            size="small"
            sx={{
              mb: 1,
              height: 22,
              fontSize: '0.72rem',
              fontWeight: 800,
              bgcolor: '#EFF6FF',
              color: '#2563EB',
              border: '1px solid #BFDBFE',
              borderRadius: 1,
            }}
          />
        )}
        <Typography
          component="h1"
          variant="h2"
          sx={{
            fontWeight: 800,
            color: 'text.primary',
            letterSpacing: '-0.02em',
            lineHeight: 1.25,
            overflowWrap: 'anywhere',
          }}
        >
          {title}
        </Typography>
        {desc && (
          <Typography
            variant="body2"
            sx={{
              color: '#475569',
              mt: 0.5,
              maxWidth: 680,
              lineHeight: 1.55,
            }}
          >
            {desc}
          </Typography>
        )}
      </Box>
      {acts && (
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
          {acts}
        </Box>
      )}
    </Box>
  );
};

export default PageHeader;
