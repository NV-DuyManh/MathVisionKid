import React from 'react';
import { Box, Typography, Chip } from '@mui/material';

export interface PageHeaderProps {
  title: string;
  description?: string;
  subtitle?: string;
  badge?: string;
  actions?: React.ReactNode;
  action?: React.ReactNode;
  back?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  subtitle,
  badge,
  actions,
  action,
  back,
}) => {
  const desc = description || subtitle;
  const acts = actions || action;

  return (
    <Box
      component="header"
      className="teacher-page-header"
    >
      <Box sx={{ minWidth: 0 }}>
        {back && <Box sx={{ mb: 1 }}>{back}</Box>}
        {badge && (
          <Chip
            label={badge}
            size="small"
            sx={{
              mb: 1,
              height: 22,
              fontSize: '0.72rem',
              fontWeight: 800,
              bgcolor: 'primary.light',
              color: 'primary.dark',
              borderRadius: '6px',
            }}
          />
        )}
        <Typography
          component="h1"
          variant="h3"
          sx={{
            fontWeight: 800,
            color: 'text.primary',
            fontSize: { xs: '1.55rem', md: '2rem' },
            overflowWrap: 'anywhere',
            letterSpacing: '-0.02em',
            lineHeight: 1.25,
          }}
        >
          {title}
        </Typography>
        {desc && (
          <Typography
            variant="body2"
            sx={{
              color: 'text.secondary',
              mt: 0.75,
              maxWidth: 680,
              lineHeight: 1.55,
            }}
          >
            {desc}
          </Typography>
        )}
      </Box>
      {acts && (
        <Box className="teacher-page-actions">
          {acts}
        </Box>
      )}
    </Box>
  );
};

export default PageHeader;
