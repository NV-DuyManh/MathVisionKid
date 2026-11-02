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
    textColor: '#2563EB',
    borderColor: '#BFDBFE',
  },
  PROCESSING: {
    label: 'Đang xử lý',
    color: 'info',
    icon: <Sync sx={{ fontSize: '14px !important', animation: 'spin 2s linear infinite' }} />,
    bgColor: '#EFF6FF',
    textColor: '#2563EB',
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
    textColor: '#DC2626',
    borderColor: '#FECACA',
  },
  NEEDS_CONFIRMATION: {
    label: 'Cần xác nhận',
    color: 'warning',
    icon: <HelpOutlined sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FFFBEB',
    textColor: '#D97706',
    borderColor: '#FDE68A',
  },
  NEEDS_RETAKE: {
    label: 'Cần chụp lại',
    color: 'warning',
    icon: <ImageNotSupported sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FFFBEB',
    textColor: '#D97706',
    borderColor: '#FDE68A',
  },
  CROP_REQUIRED: {
    label: 'Cần cắt vùng bài',
    color: 'warning',
    icon: <Crop sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FFFBEB',
    textColor: '#D97706',
    borderColor: '#FDE68A',
  },
  FEEDBACK_READY: {
    label: 'Có phản hồi',
    color: 'info',
    icon: <PendingActions sx={{ fontSize: '14px !important' }} />,
    bgColor: '#EFF6FF',
    textColor: '#2563EB',
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
    bgColor: '#ECFDF5',
    textColor: '#059669',
    borderColor: '#A7F3D0',
  },
  TEACHER_OVERRIDDEN: {
    label: 'Giáo viên đã điều chỉnh',
    color: 'info',
    icon: <Edit sx={{ fontSize: '14px !important' }} />,
    bgColor: '#EFF6FF',
    textColor: '#1D4ED8',
    borderColor: '#BFDBFE',
  },
  FAILED: {
    label: 'Lỗi xử lý',
    color: 'error',
    icon: <ErrorOutlined sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FEF2F2',
    textColor: '#DC2626',
    borderColor: '#FECACA',
  },

  // Batch Statuses
  UPLOADING: {
    label: 'Đang tải lên',
    color: 'info',
    icon: <Sync sx={{ fontSize: '14px !important' }} />,
    bgColor: '#EFF6FF',
    textColor: '#2563EB',
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
    bgColor: '#ECFDF5',
    textColor: '#059669',
    borderColor: '#A7F3D0',
  },
  PARTIAL: {
    label: 'Hoàn thành một phần',
    color: 'warning',
    icon: <Warning sx={{ fontSize: '14px !important' }} />,
    bgColor: '#FFFBEB',
    textColor: '#D97706',
    borderColor: '#FDE68A',
  },

  // Assignment Statuses
  ACTIVE: {
    label: 'Đang hoạt động',
    color: 'success',
    icon: <CheckCircle sx={{ fontSize: '14px !important' }} />,
    bgColor: '#ECFDF5',
    textColor: '#059669',
    borderColor: '#A7F3D0',
  },
  ARCHIVED: {
    label: 'Đã lưu trữ',
    color: 'default',
    icon: <HourglassEmpty sx={{ fontSize: '14px !important' }} />,
    bgColor: '#F1F5F9',
    textColor: '#475569',
    borderColor: '#CBD5E1',
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
        height: 24,
        fontSize: '0.72rem',
        fontWeight: 800,
        letterSpacing: '0.01em',
        borderRadius: 1.5,
        backgroundColor: config.bgColor,
        color: config.textColor,
        border: `1px solid ${config.borderColor}`,
        '& .MuiChip-icon': {
          color: 'inherit',
          marginLeft: '6px',
        },
        '& .MuiChip-label': {
          paddingLeft: '6px',
          paddingRight: '8px',
        },
        ...sx,
      }}
      {...props}
    />
  );
};

export default StatusChip;
