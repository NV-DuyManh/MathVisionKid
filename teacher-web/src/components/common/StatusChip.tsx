import React from 'react';
import { Chip, type ChipProps } from '@mui/material';
import {
  CheckCircle,
  Warning,
  HourglassEmpty,
  ErrorOutlined,
  AutoAwesome,
  Edit,
  PendingActions,
  Crop,
  ImageNotSupported,
  Sync,
  HelpOutlined,
} from '@mui/icons-material';

interface StatusConfig {
  label: string;
  color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  icon: React.ReactElement;
  bgColor?: string;
  textColor?: string;
  borderColor?: string;
}

const STATUS_MAP: Record<string, StatusConfig> = {
  // Submission Statuses
  CREATED: {
    label: 'Mới tạo',
    color: 'default',
    icon: <HourglassEmpty sx={{ fontSize: '14px !important' }} />,
    bgColor: '#F1F5F9',
    textColor: '#475569',
    borderColor: '#CBD5E1',
  },
  IMAGE_UPLOADED: {
    label: 'Đã tải ảnh',
    color: 'info',
    icon: <HourglassEmpty sx={{ fontSize: '14px !important' }} />,
    bgColor: '#EFF6FF',
    textColor: '#1D4ED8',
    borderColor: '#BFDBFE',
  },
  PROCESSING: {
    label: 'Đang xử lý',
    color: 'info',
    icon: <Sync sx={{ fontSize: '14px !important', animation: 'spin 2s linear infinite' }} />,
    bgColor: '#EFF6FF',
    textColor: '#1D4ED8',
    borderColor: '#BFDBFE',
  },
  PROPOSED_GRADE: {
    label: 'AI đề xuất',
    color: 'primary',
    icon: <AutoAwesome sx={{ fontSize: '14px !important' }} />,
    bgColor: '#EFF6FF',
    textColor: '#1D4ED8',
    borderColor: '#93C5FD',
  },
  REVIEW_REQUIRED: {
    label: 'Cần xem lại',
    color: 'error',
    icon: <Warning sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FEF2F2',
    textColor: '#991B1B',
    borderColor: '#FCA5A5',
  },
  NEEDS_CONFIRMATION: {
    label: 'Cần xác nhận',
    color: 'warning',
    icon: <HelpOutlined sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FEF3C7',
    textColor: '#B45309',
    borderColor: '#FCD34D',
  },
  NEEDS_RETAKE: {
    label: 'Cần chụp lại',
    color: 'warning',
    icon: <ImageNotSupported sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FEF3C7',
    textColor: '#B45309',
    borderColor: '#FCD34D',
  },
  CROP_REQUIRED: {
    label: 'Cần cắt vùng bài',
    color: 'warning',
    icon: <Crop sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FEF3C7',
    textColor: '#B45309',
    borderColor: '#FCD34D',
  },
  FEEDBACK_READY: {
    label: 'Có phản hồi',
    color: 'info',
    icon: <PendingActions sx={{ fontSize: '14px !important' }} />,
    bgColor: '#EFF6FF',
    textColor: '#1D4ED8',
    borderColor: '#BFDBFE',
  },
  OUT_OF_SCOPE: {
    label: 'Ngoài phạm vi',
    color: 'default',
    icon: <HelpOutlined sx={{ fontSize: '14px !important' }} />,
    bgColor: '#F1F5F9',
    textColor: '#475569',
    borderColor: '#CBD5E1',
  },
  TEACHER_APPROVED: {
    label: 'Giáo viên đã duyệt',
    color: 'success',
    icon: <CheckCircle sx={{ fontSize: '14px !important' }} />,
    bgColor: '#DCFCE7',
    textColor: '#15803D',
    borderColor: '#86EFAC',
  },
  TEACHER_OVERRIDDEN: {
    label: 'Giáo viên đã điều chỉnh',
    color: 'primary',
    icon: <Edit sx={{ fontSize: '14px !important' }} />,
    bgColor: '#EDE9FE',
    textColor: '#6D28D9',
    borderColor: '#DDD6FE',
  },
  FAILED: {
    label: 'Lỗi xử lý',
    color: 'error',
    icon: <ErrorOutlined sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FEF2F2',
    textColor: '#991B1B',
    borderColor: '#FCA5A5',
  },

  // Batch Statuses
  UPLOADING: {
    label: 'Đang tải lên',
    color: 'info',
    icon: <Sync sx={{ fontSize: '14px !important' }} />,
    bgColor: '#EFF6FF',
    textColor: '#1D4ED8',
    borderColor: '#BFDBFE',
  },
  QUEUED: {
    label: 'Chờ xử lý',
    color: 'default',
    icon: <HourglassEmpty sx={{ fontSize: '14px !important' }} />,
    bgColor: '#F1F5F9',
    textColor: '#475569',
    borderColor: '#CBD5E1',
  },
  COMPLETED: {
    label: 'Hoàn thành',
    color: 'success',
    icon: <CheckCircle sx={{ fontSize: '14px !important' }} />,
    bgColor: '#DCFCE7',
    textColor: '#15803D',
    borderColor: '#86EFAC',
  },
  PARTIAL: {
    label: 'Hoàn thành một phần',
    color: 'warning',
    icon: <Warning sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FEF3C7',
    textColor: '#B45309',
    borderColor: '#FCD34D',
  },
};

interface StatusChipProps extends Omit<ChipProps, 'color'> {
  status: string;
}

export const StatusChip: React.FC<StatusChipProps> = ({ status, sx, ...props }) => {
  const config = STATUS_MAP[status] || {
    label: status,
    color: 'default' as const,
    icon: <HelpOutlined sx={{ fontSize: '14px !important' }} />,
    bgColor: '#F1F5F9',
    textColor: '#475569',
    borderColor: '#CBD5E1',
  };

  return (
    <Chip
      size="small"
      icon={config.icon}
      label={config.label}
      sx={{
        fontWeight: 600,
        fontSize: '0.8125rem',
        borderRadius: 1.5,
        backgroundColor: config.bgColor,
        color: config.textColor,
        border: `1px solid ${config.borderColor}`,
        '& .MuiChip-icon': {
          color: `${config.textColor} !important`,
          marginLeft: '6px',
        },
        ...sx,
      }}
      {...props}
    />
  );
};
