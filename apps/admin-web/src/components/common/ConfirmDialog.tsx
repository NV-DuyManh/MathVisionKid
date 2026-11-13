import React from 'react';
import { RequestError } from './RequestError';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  CircularProgress,
} from '@mui/material';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isDestructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
  error?: unknown;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmText = 'Xác nhận',
  cancelText = 'Hủy bỏ',
  isDestructive = false,
  onConfirm,
  onCancel,
  loading = false,
  error,
}) => {
  const titleId = React.useId();
  const descriptionId = React.useId();
  return (
    <Dialog open={open} onClose={loading ? undefined : onCancel} maxWidth="xs" fullWidth aria-labelledby={titleId} aria-describedby={descriptionId}
      slotProps={{ paper: { sx: { bgcolor: 'background.paper', backgroundImage: 'none' } } }}>
      <DialogTitle id={titleId}>{title}</DialogTitle>
      <DialogContent>
        <RequestError error={error} />
        <DialogContentText id={descriptionId} sx={{ color: 'text.secondary', fontSize: '0.95rem', overflowWrap: 'anywhere' }}>
          {message}
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2.5, flexWrap: 'wrap', gap: 1 }}>
        <Button autoFocus onClick={onCancel} disabled={loading}>
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          disabled={loading}
          aria-busy={loading}
          startIcon={loading ? <CircularProgress size={18} color="inherit" aria-hidden /> : undefined}
          variant="contained"
          color={isDestructive ? 'error' : 'primary'}
        >
          {loading ? 'Đang xử lý…' : confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
