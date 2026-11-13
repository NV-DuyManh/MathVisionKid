import React from 'react';
import { Card, CardContent, Box, Typography, Skeleton } from '@mui/material';
import ArrowForward from '@mui/icons-material/ArrowForward';
import { Link } from 'react-router-dom';

export interface StatCardProps {
  title: string;
  value: string | number | undefined | null;
  loading?: boolean;
  description: string;
  icon: React.ReactNode;
  tone?: string;
  color?: string;
  path?: string;
  linkText?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  loading = false,
  description,
  icon,
  tone = '#ECFDF5',
  color = '#047857',
  path,
  linkText = 'Xem chi tiết',
}) => {
  const content = (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        borderRadius: '12px',
        bgcolor: 'background.paper',
        '&:hover': path
          ? {
              borderColor: 'primary.main',
            }
          : undefined,
      }}
    >
      <CardContent sx={{ p: { xs: 1.5, sm: 2 }, '&:last-child': { pb: 1.5 } }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column-reverse', sm: 'row' }, gap: 1,
          justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 0.75 }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 800,
              color: 'text.secondary',
              fontSize: '0.8rem',
            }}
          >
            {title}
          </Typography>
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: '8px',
              bgcolor: tone,
              color: color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {icon}
          </Box>
        </Box>

        <Typography
          variant="h3"
          component="div"
          sx={{
            fontWeight: 900,
            color: 'text.primary',
            fontSize: { xs: '1.85rem', sm: '2.1rem' },
            letterSpacing: '-0.03em',
            lineHeight: 1.15,
            my: 0.75,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {loading ? (
            <Skeleton width={70} />
          ) : value !== undefined && value !== null ? (
            typeof value === 'number' ? value.toLocaleString('vi-VN') : value
          ) : (
            '—'
          )}
        </Typography>

        <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.78rem', display: 'block', lineHeight: 1.4 }}>
          {description}
        </Typography>

        {path && (
          <Box
            sx={{
              mt: 1,
              pt: 1,
              borderTop: 1,
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: color,
            }}
          >
            <Typography variant="caption" sx={{ fontWeight: 800, fontSize: '0.78rem', color: 'primary.dark' }}>
              {linkText}
            </Typography>
            <ArrowForward sx={{ fontSize: 16 }} />
          </Box>
        )}
      </CardContent>
    </Card>
  );

  if (path) {
    return (
      <Box
        component={Link}
        to={path}
        sx={{
          textDecoration: 'none',
          display: 'block',
          height: '100%',
          borderRadius: '12px',
          '&:hover': { textDecoration: 'none' },
        }}
      >
        {content}
      </Box>
    );
  }

  return content;
};

export default StatCard;
