import { Box, TableContainer, Typography } from '@mui/material';
import type { ReactNode } from 'react';

export function LedgerTable({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Box sx={{ minWidth: 0 }}>
      <Typography variant="body2" sx={{ display: { xs: 'block', md: 'none' }, px: 2, py: 1, bgcolor: 'background.paper' }}>
        Cuộn ngang bảng để xem thêm cột và thao tác.
      </Typography>
      <TableContainer
        role="region"
        aria-label={label}
        tabIndex={0}
        className="ledger-table"
        sx={{ border: 0, borderRadius: 0, boxShadow: 'none', '&:focus-visible': { outlineOffset: '-3px' } }}
      >
        {children}
      </TableContainer>
    </Box>
  );
}
