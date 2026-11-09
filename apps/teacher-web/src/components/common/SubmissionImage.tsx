import { useEffect, useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Box, Alert, CircularProgress } from '@mui/material';
import apiClient from '../../services/api/apiClient';
import { useMocks } from '../../config/runtime';

export interface ImageStatus {
  ready: boolean;
  reason?: string;
}

export interface SubmissionImageProps {
  id: string;
  mockUrl?: string;
  studentName?: string;
  onStatusChange?: (status: ImageStatus) => void;
}

function ZoomInIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="11" y1="8" x2="11" y2="14" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function ZoomOutIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function ResetIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
    </svg>
  );
}

function RotateIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.85.83 6.72 2.24L21 8" />
      <path d="M21 3v5h-5" />
    </svg>
  );
}

function FullscreenIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M23 4v6h-6" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  );
}

export function SubmissionImage({ id, mockUrl, studentName, onStatusChange }: SubmissionImageProps) {
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [rotation, setRotation] = useState<number>(0);
  const [fullscreenOpen, setFullscreenOpen] = useState<boolean>(false);
  const [decodeError, setDecodeError] = useState<string | null>(null);
  const [naturalDimensions, setNaturalDimensions] = useState<{ width: number; height: number } | null>(null);
  const [loaded, setLoaded] = useState<{ blob: Blob; url: string } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const image = useQuery({
    queryKey: ['submissionImage', id],
    enabled: !!id && !useMocks,
    queryFn: async ({ signal }) => {
      const response = await apiClient.get<Blob>(`/teacher/submissions/${encodeURIComponent(id)}/image`, {
        responseType: 'blob',
        signal,
      });
      return response.data;
    },
    staleTime: 60_000,
    retry: false,
  });

  useEffect(() => {
    setZoomLevel(1);
    setRotation(0);
    setDecodeError(null);
    setNaturalDimensions(null);
  }, [id]);

  useEffect(() => {
    if (useMocks && mockUrl) {
      return;
    }
    if (!image.data) return;

    if (image.data.size === 0) {
      setDecodeError('Tệp ảnh rỗng (0 byte), không có dữ liệu để hiển thị.');
      onStatusChange?.({ ready: false, reason: 'Tệp ảnh rỗng (0 byte)' });
      return;
    }

    const url = URL.createObjectURL(image.data);
    setLoaded({ blob: image.data, url });
    return () => {
      URL.revokeObjectURL(url);
    };
  }, [image.data, mockUrl, onStatusChange]);

  useEffect(() => {
    if (image.isLoading) {
      onStatusChange?.({ ready: false, reason: 'Đang tải ảnh bài làm...' });
    } else if (image.isError) {
      onStatusChange?.({ ready: false, reason: 'Không thể tải ảnh bài làm từ máy chủ' });
    }
  }, [image.isLoading, image.isError, onStatusChange]);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const nw = img.naturalWidth;
    const nh = img.naturalHeight;

    // Check for degenerate image in environments where naturalWidth is supported (> 0)
    if (nw > 0 && nh > 0 && (nw <= 10 || nh <= 10)) {
      const msg = `Ảnh bài làm không hợp lệ hoặc kích thước quá nhỏ (${nw}×${nh}px), không đủ độ phân giải để đọc bài làm.`;
      setDecodeError(msg);
      onStatusChange?.({ ready: false, reason: `Ảnh quá nhỏ (${nw}×${nh}px), không đọc được` });
      return;
    }

    setDecodeError(null);
    if (nw > 0 && nh > 0) {
      setNaturalDimensions({ width: nw, height: nh });
    }
    onStatusChange?.({ ready: true });
  };

  const handleImageError = () => {
    const msg = 'Chưa giải mã được ảnh bài làm. Định dạng ảnh có thể bị hỏng hoặc không được hỗ trợ.';
    setDecodeError(msg);
    onStatusChange?.({ ready: false, reason: 'Lỗi giải mã ảnh bài làm' });
  };

  const src = useMocks ? mockUrl : loaded && loaded.blob === image.data ? loaded.url : undefined;

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(3, +(prev + 0.25).toFixed(2)));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(1, +(prev - 0.25).toFixed(2)));
  const handleResetZoom = () => {
    setZoomLevel(1);
    setRotation(0);
  };
  const handleRotate = () => setRotation((prev) => (prev + 90) % 360);

  if (image.isLoading && !useMocks) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 4, minHeight: 320 }}>
        <CircularProgress aria-label="Đang tải ảnh bài làm" size={44} sx={{ color: '#A78BFA' }} />
        <Box component="span" sx={{ mt: 2, color: '#E9E2F2', fontWeight: 600, fontSize: '0.875rem' }}>
          Đang tải ảnh bài làm học sinh...
        </Box>
      </Box>
    );
  }

  if (image.isError && !useMocks) {
    return (
      <Box sx={{ p: 3, maxWidth: 480, mx: 'auto', textAlign: 'center' }}>
        <Alert severity="error" sx={{ mb: 2, textAlign: 'left' }} role="alert">
          Chưa tải được ảnh bài làm từ máy chủ. Vui lòng kiểm tra quyền truy cập hoặc thử tải lại.
        </Alert>
        <Box
          component="button"
          onClick={() => void image.refetch()}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 1,
            px: 2.5,
            py: 1,
            bgcolor: '#7C3AED',
            color: 'white',
            border: 'none',
            borderRadius: 1.5,
            fontWeight: 700,
            cursor: 'pointer',
            fontSize: '0.875rem',
            '&:hover': { bgcolor: '#6D28D9' },
          }}
        >
          <RefreshIcon /> Thử lại tải ảnh
        </Box>
      </Box>
    );
  }

  if (decodeError) {
    return (
      <Box sx={{ p: 3, maxWidth: 520, mx: 'auto', textAlign: 'center' }}>
        <Alert severity="error" sx={{ mb: 2, textAlign: 'left' }} role="alert">
          {decodeError}
        </Alert>
        <Box
          component="button"
          onClick={() => {
            setDecodeError(null);
            void image.refetch();
          }}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 1,
            px: 2,
            py: 0.75,
            color: '#E9E2F2',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: 1.5,
            bgcolor: 'transparent',
            cursor: 'pointer',
            '&:hover': { borderColor: '#FFFFFF' },
          }}
        >
          <RefreshIcon /> Thử lại
        </Box>
      </Box>
    );
  }

  if (!src) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
        <CircularProgress aria-label="Đang chuẩn bị hiển thị ảnh" size={36} sx={{ color: '#A78BFA' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Top Floating Control Bar */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 2,
          py: 1,
          bgcolor: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box component="span" sx={{ color: '#E2E8F0', fontWeight: 700, fontSize: '0.75rem', letterSpacing: '0.02em' }}>
            BÀI LÀM GỐC
          </Box>
          {naturalDimensions && (
            <Box
              component="span"
              sx={{
                px: 1,
                py: 0.25,
                bgcolor: 'rgba(255,255,255,0.12)',
                color: '#CBD5E1',
                fontSize: '0.7rem',
                borderRadius: 1,
                fontWeight: 600,
              }}
            >
              {naturalDimensions.width} × {naturalDimensions.height}
            </Box>
          )}
          {zoomLevel > 1 && (
            <Box
              component="span"
              sx={{
                px: 1,
                py: 0.25,
                bgcolor: '#2563EB',
                color: 'white',
                fontSize: '0.7rem',
                borderRadius: 1,
                fontWeight: 700,
              }}
            >
              {Math.round(zoomLevel * 100)}%
            </Box>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box
            component="button"
            aria-label="Phóng to ảnh"
            onClick={handleZoomIn}
            disabled={zoomLevel >= 3}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 0.5,
              color: '#E2E8F0',
              bgcolor: 'transparent',
              border: 'none',
              borderRadius: 1,
              cursor: zoomLevel >= 3 ? 'default' : 'pointer',
              opacity: zoomLevel >= 3 ? 0.4 : 1,
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
            }}
          >
            <ZoomInIcon />
          </Box>

          <Box
            component="button"
            aria-label="Thu nhỏ ảnh"
            onClick={handleZoomOut}
            disabled={zoomLevel <= 1}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 0.5,
              color: '#E2E8F0',
              bgcolor: 'transparent',
              border: 'none',
              borderRadius: 1,
              cursor: zoomLevel <= 1 ? 'default' : 'pointer',
              opacity: zoomLevel <= 1 ? 0.4 : 1,
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
            }}
          >
            <ZoomOutIcon />
          </Box>

          <Box
            component="button"
            aria-label="Đặt lại kích thước"
            onClick={handleResetZoom}
            disabled={zoomLevel === 1 && rotation === 0}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 0.5,
              color: '#E2E8F0',
              bgcolor: 'transparent',
              border: 'none',
              borderRadius: 1,
              cursor: zoomLevel === 1 && rotation === 0 ? 'default' : 'pointer',
              opacity: zoomLevel === 1 && rotation === 0 ? 0.4 : 1,
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
            }}
          >
            <ResetIcon />
          </Box>

          <Box
            component="button"
            aria-label="Xoay ảnh 90 độ"
            onClick={handleRotate}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 0.5,
              color: '#E2E8F0',
              bgcolor: 'transparent',
              border: 'none',
              borderRadius: 1,
              cursor: 'pointer',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
            }}
          >
            <RotateIcon />
          </Box>

          <Box
            component="button"
            aria-label="Xem chi tiết toàn màn hình"
            onClick={() => setFullscreenOpen(true)}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 0.5,
              color: '#FCD34D',
              bgcolor: 'transparent',
              border: 'none',
              borderRadius: 1,
              cursor: 'pointer',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
            }}
          >
            <FullscreenIcon />
          </Box>
        </Box>
      </Box>

      {/* Image Display Area */}
      <Box
        ref={containerRef}
        sx={{
          width: '100%',
          minHeight: { xs: 260, md: 540 },
          maxHeight: { xs: 460, md: 720 },
          overflow: zoomLevel > 1 ? 'auto' : 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2,
          bgcolor: '#191332',
          cursor: zoomLevel > 1 ? 'grab' : 'zoom-in',
          userSelect: 'none',
        }}
        onClick={(e) => {
          if (e.target === e.currentTarget || (e.target as HTMLElement).tagName === 'IMG') {
            if (zoomLevel === 1) handleZoomIn();
          }
        }}
      >
        <Box
          component="img"
          src={src}
          alt={`Bài làm của ${studentName || 'học sinh'}`}
          onLoad={handleImageLoad}
          onError={handleImageError}
          sx={{
            maxWidth: zoomLevel === 1 ? '100%' : 'none',
            maxHeight: zoomLevel === 1 ? 650 : 'none',
            width: zoomLevel > 1 && naturalDimensions ? `${naturalDimensions.width * zoomLevel}px` : 'auto',
            objectFit: 'contain',
            borderRadius: 1.5,
            transform: rotation !== 0 ? `rotate(${rotation}deg)` : undefined,
            transition: 'transform 0.2s ease-out, width 0.2s ease-out',
            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.45)',
          }}
        />
      </Box>

      {/* Fullscreen Overlay View for Detail Inspection */}
      {fullscreenOpen && (
        <Box
          role="dialog"
          aria-modal="true"
          aria-label="Xem chi tiết toàn màn hình"
          sx={{
            position: 'fixed',
            inset: 0,
            zIndex: 1400,
            bgcolor: '#0B0F19',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              bgcolor: '#0F172A',
              color: 'white',
              py: 1.5,
              px: 2.5,
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box component="span" sx={{ fontWeight: 700, fontSize: '1rem' }}>
                Chi tiết bài làm: {studentName || 'Học sinh'}
              </Box>
              {naturalDimensions && (
                <Box
                  component="span"
                  sx={{
                    px: 1,
                    py: 0.25,
                    bgcolor: 'rgba(255,255,255,0.15)',
                    color: '#E2E8F0',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    borderRadius: 1,
                  }}
                >
                  Độ phân giải: {naturalDimensions.width} × {naturalDimensions.height}px
                </Box>
              )}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                component="button"
                aria-label="Thu nhỏ trong modal"
                onClick={handleZoomOut}
                disabled={zoomLevel <= 1}
                sx={{
                  color: '#E2E8F0',
                  bgcolor: 'transparent',
                  border: 'none',
                  p: 0.5,
                  cursor: zoomLevel <= 1 ? 'default' : 'pointer',
                  opacity: zoomLevel <= 1 ? 0.4 : 1,
                }}
              >
                <ZoomOutIcon />
              </Box>
              <Box
                component="button"
                aria-label="Phóng to trong modal"
                onClick={handleZoomIn}
                disabled={zoomLevel >= 3}
                sx={{
                  color: '#E2E8F0',
                  bgcolor: 'transparent',
                  border: 'none',
                  p: 0.5,
                  cursor: zoomLevel >= 3 ? 'default' : 'pointer',
                  opacity: zoomLevel >= 3 ? 0.4 : 1,
                }}
              >
                <ZoomInIcon />
              </Box>
              <Box
                component="button"
                aria-label="Đặt lại trong modal"
                onClick={handleResetZoom}
                sx={{ color: '#E2E8F0', bgcolor: 'transparent', border: 'none', p: 0.5, cursor: 'pointer' }}
              >
                <ResetIcon />
              </Box>
              <Box
                component="button"
                aria-label="Xoay ảnh trong modal"
                onClick={handleRotate}
                sx={{ color: '#E2E8F0', bgcolor: 'transparent', border: 'none', p: 0.5, cursor: 'pointer' }}
              >
                <RotateIcon />
              </Box>
              <Box
                component="button"
                aria-label="Đóng chế độ xem toàn màn hình"
                onClick={() => setFullscreenOpen(false)}
                sx={{ color: '#CBD5E1', bgcolor: 'transparent', border: 'none', p: 0.5, cursor: 'pointer', ml: 1 }}
              >
                <CloseIcon />
              </Box>
            </Box>
          </Box>

          {/* Modal Content */}
          <Box
            sx={{
              flex: 1,
              bgcolor: '#0B0F19',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 2,
              overflow: 'auto',
            }}
          >
            <Box
              component="img"
              src={src}
              alt={`Ảnh chi tiết bài làm của ${studentName || 'học sinh'}`}
              sx={{
                maxWidth: zoomLevel === 1 ? '100%' : 'none',
                maxHeight: zoomLevel === 1 ? '80vh' : 'none',
                width: zoomLevel > 1 && naturalDimensions ? `${naturalDimensions.width * zoomLevel}px` : 'auto',
                objectFit: 'contain',
                transform: rotation !== 0 ? `rotate(${rotation}deg)` : undefined,
                transition: 'transform 0.2s ease-out, width 0.2s ease-out',
              }}
            />
          </Box>

          {/* Modal Footer */}
          <Box
            sx={{
              bgcolor: '#0F172A',
              px: 2.5,
              py: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <Box component="span" sx={{ color: '#94A3B8', fontSize: '0.8rem' }}>
              Dùng các nút điều khiển hoặc kéo cuộn để kiểm tra từng phép tính, nét chữ và phần đã che thông tin.
            </Box>
            <Box
              component="button"
              onClick={() => setFullscreenOpen(false)}
              sx={{
                px: 2,
                py: 0.5,
                color: '#E2E8F0',
                fontWeight: 600,
                bgcolor: 'rgba(255,255,255,0.1)',
                border: 'none',
                borderRadius: 1,
                cursor: 'pointer',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' },
              }}
            >
              Đóng
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}
