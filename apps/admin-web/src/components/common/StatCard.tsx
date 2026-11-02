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
  tone = '#EFF6FF',
  color = '#2563EB',
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
        borderRadius: 3.5,
        border: '1px solid #E2E8F0',
        bgcolor: '#FFFFFF',
        transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
        '&:hover': path
          ? {
              transform: 'translateY(-2px)',
              boxShadow: '0 8px 24px -4px rgba(15, 23, 42, 0.08)',
              borderColor: '#CBD5E1',
            }
          : undefined,
      }}
    >
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: path ? 1.75 : 2.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 800,
              color: '#64748B',
              fontSize: '0.8rem',
              letterSpacing: '0.02em',
              textTransform: 'uppercase',
            }}
          >
            {title}
          </Typography>
          <Box
            sx={{
              width: 38,
              height: 38,
              borderRadius: 2.5,
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
          sx={{
            fontWeight: 900,
            color: '#0F172A',
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
              mt: 2,
              pt: 1.5,
              borderTop: '1px solid #F1F5F9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: color,
            }}
          >
            <Typography variant="caption" sx={{ fontWeight: 800, fontSize: '0.78rem' }}>
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
        }}
      >
        {content}
      </Box>
    );
  }

  return content;
};

export default StatCard;
