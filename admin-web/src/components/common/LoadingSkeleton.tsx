import React from 'react';
import { Skeleton, TableRow, TableCell } from '@mui/material';

export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 5,
}) => {
  return (
    <>
      {Array.from({ length: rows }).map((_, rIdx) => (
        <TableRow key={rIdx}>
          {Array.from({ length: columns }).map((_, cIdx) => (
            <TableCell key={cIdx}>
              <Skeleton animation="wave" height={24} />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
};
