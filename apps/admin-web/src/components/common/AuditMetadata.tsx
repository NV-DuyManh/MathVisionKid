import { Box, Typography } from '@mui/material';
const SECRET = /password|passwd|token|secret|authorization|credential|cookie|api.?key|ticket|sso/i;
export function safeMetadata(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(safeMetadata);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value)
    .map(([key, item]) => [key, SECRET.test(key) ? '[Đã ẩn]' : safeMetadata(item)]));
  if (typeof value === 'string') return value
    .replace(/Bearer\s+\S+/gi, '[Đã ẩn]')
    .replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, '[Đã ẩn]');
  return value;
}
export function AuditMetadata({ metadata }: { metadata: unknown }) {
  if (!metadata || typeof metadata !== 'object' || !Object.keys(metadata).length) return <Typography color="text.secondary">Không có chi tiết bổ sung</Typography>;
  return <Box component="dl" sx={{ m: 0, display: 'grid', gap: 1.5 }}>
    {Object.entries(safeMetadata(metadata) as Record<string, unknown>).map(([key, value]) =>
      <Box key={key}><Typography component="dt" variant="caption" color="text.secondary">{key}</Typography>
        <Typography component="dd" variant="body2" sx={{ m: 0, overflowWrap: 'anywhere', whiteSpace: 'pre-wrap' }}>{typeof value === 'string' ? value : JSON.stringify(value, null, 2)}</Typography></Box>)}
  </Box>;
}
