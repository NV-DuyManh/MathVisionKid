import React, { useEffect, useState, useRef, useCallback } from 'react';
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

type ToolMode = 'pen' | 'highlight' | 'circle' | 'check' | 'cross' | 'star' | null;

interface StrokePoint {
  nx: number; // Normalized X (0.0 to 1.0)
  ny: number; // Normalized Y (0.0 to 1.0)
}

interface Stroke {
  points: StrokePoint[];
  color: string;
  width: number;
}

interface Stamp {
  nx: number;
  ny: number;
  type: 'check' | 'cross' | 'circle' | 'star';
}

function ZoomInIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="11" y1="8" x2="11" y2="14" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function ZoomOutIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function ResetIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
    </svg>
  );
}

function RotateIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.85.83 6.72 2.24L21 8" />
      <path d="M21 3v5h-5" />
    </svg>
  );
}

function FullscreenIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M23 4v6h-6" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  );
}

function loadSubmissionAnnotations(subId?: string): { strokes: Stroke[]; stamps: Stamp[] } {
  if (!subId || typeof window === 'undefined') return { strokes: [], stamps: [] };
  try {
    const raw = window.sessionStorage?.getItem(`mvk_annotations_${subId}`);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed?.strokes) && Array.isArray(parsed?.stamps)) {
        return { strokes: parsed.strokes, stamps: parsed.stamps };
      }
    }
  } catch {
    // SessionStorage may be restricted or unavailable
  }
  return { strokes: [], stamps: [] };
}

function saveSubmissionAnnotations(subId: string | undefined, strokes: Stroke[], stamps: Stamp[]) {
  if (!subId || typeof window === 'undefined') return;
  try {
    if (strokes.length > 0 || stamps.length > 0) {
      window.sessionStorage?.setItem(`mvk_annotations_${subId}`, JSON.stringify({ strokes, stamps }));
    } else {
      window.sessionStorage?.removeItem(`mvk_annotations_${subId}`);
    }
  } catch {
    // SessionStorage quota exceeded or restricted
  }
}

export function SubmissionImage({ id, mockUrl, studentName, onStatusChange }: SubmissionImageProps) {
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [rotation, setRotation] = useState<number>(0);
  const [fullscreenOpen, setFullscreenOpen] = useState<boolean>(false);
  const [decodeError, setDecodeError] = useState<string | null>(null);
  const [naturalDimensions, setNaturalDimensions] = useState<{ width: number; height: number } | null>(null);
  const [retryCount, setRetryCount] = useState<number>(0);
  const [loaded, setLoaded] = useState<{ blob: Blob; url: string; retryCount: number } | null>(null);

  // Interactive Teacher Canvas State with per-submission persistence
  const initialAnnotations = loadSubmissionAnnotations(id);
  const [activeTool, setActiveTool] = useState<ToolMode>('pen');
  const [strokes, setStrokes] = useState<Stroke[]>(initialAnnotations.strokes);
  const [stamps, setStamps] = useState<Stamp[]>(initialAnnotations.stamps);
  const [isDrawing, setIsDrawing] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);
  const currentStroke = useRef<StrokePoint[]>([]);

  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fullscreenTriggerRef = useRef<HTMLButtonElement | null>(null);
  const fullscreenModalRef = useRef<HTMLDivElement | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);

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

  const [prevId, setPrevId] = useState<string | undefined>(id);
  if (id !== prevId) {
    setPrevId(id);
    setZoomLevel(1);
    setRotation(0);
    setDecodeError(null);
    setNaturalDimensions(null);
    setRetryCount(0);
    const saved = loadSubmissionAnnotations(id);
    setStrokes(saved.strokes);
    setStamps(saved.stamps);
  }

  useEffect(() => {
    saveSubmissionAnnotations(id, strokes, stamps);
  }, [id, strokes, stamps]);

  useEffect(() => {
    currentStroke.current = [];
  }, [id]);

  const isZeroByte = !useMocks && !image.isFetching && !!image.data && image.data.size === 0;
  const effectiveError = decodeError || (isZeroByte ? 'Tệp ảnh rỗng (0 byte), không có dữ liệu để hiển thị.' : null);

  useEffect(() => {
    if (useMocks && mockUrl) {
      return;
    }
    if (image.isFetching) return;
    if (!image.data) return;

    if (image.data.size === 0) {
      onStatusChange?.({ ready: false, reason: 'Tệp ảnh rỗng (0 byte)' });
      return;
    }

    const url = URL.createObjectURL(image.data);
    setLoaded({ blob: image.data, url, retryCount });
    return () => {
      URL.revokeObjectURL(url);
    };
  }, [image.data, image.isFetching, mockUrl, retryCount, onStatusChange]);

  useEffect(() => {
    if (useMocks) {
      if (mockUrl) onStatusChange?.({ ready: true });
      return;
    }
    if (image.isLoading || image.isFetching) {
      onStatusChange?.({ ready: false, reason: 'Đang tải ảnh bài làm...' });
    } else if (image.isError) {
      onStatusChange?.({ ready: false, reason: 'Không thể tải ảnh bài làm từ máy chủ' });
    }
  }, [image.isLoading, image.isFetching, image.isError, mockUrl, onStatusChange]);

  const handleRetry = async () => {
    setDecodeError(null);
    setNaturalDimensions(null);
    if (loaded?.url) {
      URL.revokeObjectURL(loaded.url);
    }
    setLoaded(null);
    onStatusChange?.({ ready: false, reason: 'Đang tải lại ảnh bài làm...' });
    setRetryCount((prev) => prev + 1);
    await image.refetch();
  };

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const nw = img.naturalWidth;
    const nh = img.naturalHeight;

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
    const msg =
      'Chưa giải mã được ảnh bài làm trong trình duyệt. Tệp có thể thuộc định dạng Apple HEIC/HEIF hoặc bị gián đoạn truyền tải.';
    setDecodeError(msg);
    onStatusChange?.({ ready: false, reason: 'Lỗi giải mã ảnh bài làm' });
  };

  const handleOpenFullscreen = (e: React.MouseEvent<HTMLButtonElement>) => {
    fullscreenTriggerRef.current = e.currentTarget;
    setFullscreenOpen(true);
  };

  const handleCloseFullscreen = useCallback(() => {
    setFullscreenOpen(false);
    setTimeout(() => {
      fullscreenTriggerRef.current?.focus();
    }, 0);
  }, []);

  // Modal accessibility
  useEffect(() => {
    if (!fullscreenOpen) return;

    const doc = typeof document !== 'undefined' ? document : null;
    const win = typeof window !== 'undefined' ? window : null;

    const originalOverflow = doc ? doc.body.style.overflow : '';
    if (doc) {
      doc.body.style.overflow = 'hidden';
    }

    const focusTimer = setTimeout(() => {
      closeButtonRef.current?.focus();
    }, 50);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleCloseFullscreen();
        return;
      }

      if (e.key === 'Tab' && fullscreenModalRef.current) {
        const focusableElements = fullscreenModalRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        const focusable = Array.from(focusableElements);
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (doc && doc.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (doc && doc.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };

    if (win) {
      win.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      clearTimeout(focusTimer);
      if (doc) {
        doc.body.style.overflow = originalOverflow;
      }
      if (win) {
        win.removeEventListener('keydown', handleKeyDown);
      }
    };
  }, [fullscreenOpen, handleCloseFullscreen]);

  const src = useMocks
    ? mockUrl
    : loaded && loaded.retryCount === retryCount && loaded.blob === image.data
    ? loaded.url
    : undefined;

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(3, +(prev + 0.25).toFixed(2)));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(1, +(prev - 0.25).toFixed(2)));
  const handleResetZoom = () => {
    setZoomLevel(1);
    setRotation(0);
  };
  const handleRotate = () => setRotation((prev) => (prev + 90) % 360);

  // Compute layout dimensions for zoom and rotation
  const baseWidth = naturalDimensions ? Math.min(naturalDimensions.width, 640) : 640;
  const aspectRatio = naturalDimensions && naturalDimensions.width > 0
    ? naturalDimensions.height / naturalDimensions.width
    : 0.75;
  const baseHeight = Math.round(baseWidth * aspectRatio);

  const renderedWidth = Math.round(baseWidth * zoomLevel);
  const renderedHeight = Math.round(baseHeight * zoomLevel);

  const isRotated = (rotation % 180) !== 0;
  const fitToViewport = zoomLevel === 1 && !isRotated;
  const boxWidth = isRotated ? renderedHeight : renderedWidth;
  const boxHeight = isRotated ? renderedWidth : renderedHeight;

  // -------------------------------------------------------------------
  // TEACHER ANNOTATION CANVAS ENGINE (Universal Aspect Ratio & Scaling)
  // -------------------------------------------------------------------
  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext ? canvas.getContext('2d') : null;
    if (!ctx) return;

    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;

    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    if (showOverlay) {
      // Draw completed strokes
      strokes.forEach((stroke) => {
        if (stroke.points.length < 2) return;
        ctx.beginPath();
        ctx.strokeStyle = stroke.color;
        ctx.lineWidth = stroke.width;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        ctx.moveTo(stroke.points[0].nx * w, stroke.points[0].ny * h);
        for (let i = 1; i < stroke.points.length; i++) {
          ctx.lineTo(stroke.points[i].nx * w, stroke.points[i].ny * h);
        }
        ctx.stroke();
      });

      // Draw active stroke
      if (currentStroke.current.length > 1) {
        ctx.beginPath();
        const isHl = activeTool === 'highlight';
        ctx.strokeStyle = isHl ? 'rgba(234, 179, 8, 0.45)' : '#EF4444';
        ctx.lineWidth = isHl ? 16 : 3;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        ctx.moveTo(currentStroke.current[0].nx * w, currentStroke.current[0].ny * h);
        for (let i = 1; i < currentStroke.current.length; i++) {
          ctx.lineTo(currentStroke.current[i].nx * w, currentStroke.current[i].ny * h);
        }
        ctx.stroke();
      }

      // Draw stamps (check, cross, circle, star)
      stamps.forEach((stamp) => {
        const sx = stamp.nx * w;
        const sy = stamp.ny * h;
        ctx.save();
        ctx.font = 'bold 24px Arial, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        if (stamp.type === 'check') {
          ctx.fillStyle = '#10B981';
          ctx.fillText('✓', sx, sy);
        } else if (stamp.type === 'cross') {
          ctx.fillStyle = '#EF4444';
          ctx.fillText('✗', sx, sy);
        } else if (stamp.type === 'circle') {
          ctx.strokeStyle = '#EF4444';
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.arc(sx, sy, 20, 0, 2 * Math.PI);
          ctx.stroke();
        } else if (stamp.type === 'star') {
          ctx.fillStyle = '#F59E0B';
          ctx.fillText('⭐', sx, sy);
        }
        ctx.restore();
      });
    }
    ctx.restore();
  }, [strokes, stamps, showOverlay, activeTool]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    if (!parent) return;

    const rect = parent.getBoundingClientRect ? parent.getBoundingClientRect() : { width: renderedWidth, height: renderedHeight };
    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
    const displayW = Math.max(rect.width || renderedWidth || 300, 10);
    const displayH = Math.max(rect.height || renderedHeight || 300, 10);

    canvas.width = Math.round(displayW * dpr);
    canvas.height = Math.round(displayH * dpr);

    redraw();
  }, [renderedWidth, renderedHeight, boxWidth, boxHeight, rotation, zoomLevel, redraw]);

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>): StrokePoint => {
    const canvas = canvasRef.current;
    if (!canvas || !canvas.getBoundingClientRect) return { nx: 0, ny: 0 };
    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e && e.touches.length > 0 ? e.touches[0].clientX : (e as React.MouseEvent).clientX;
    const clientY = 'touches' in e && e.touches.length > 0 ? e.touches[0].clientY : (e as React.MouseEvent).clientY;
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    const nx = rect.width > 0 ? Math.max(0, Math.min(1, x / rect.width)) : 0;
    const ny = rect.height > 0 ? Math.max(0, Math.min(1, y / rect.height)) : 0;
    return { nx, ny };
  };

  const handlePointerDown = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!showOverlay || !activeTool) return;
    const coords = getCanvasCoords(e);

    if (activeTool === 'pen' || activeTool === 'highlight') {
      setIsDrawing(true);
      currentStroke.current = [coords];
    } else {
      setStamps((prev) => [...prev, { nx: coords.nx, ny: coords.ny, type: activeTool as Stamp['type'] }]);
    }
  };

  const handlePointerMove = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing || (!activeTool && activeTool !== 'pen' && activeTool !== 'highlight')) return;
    const coords = getCanvasCoords(e);
    currentStroke.current.push(coords);
    redraw();
  };

  const handlePointerUp = () => {
    if (isDrawing && currentStroke.current.length > 0) {
      const isHl = activeTool === 'highlight';
      setStrokes((prev) => [
        ...prev,
        {
          points: [...currentStroke.current],
          color: isHl ? 'rgba(234, 179, 8, 0.45)' : '#EF4444',
          width: isHl ? 16 : 3,
        },
      ]);
      currentStroke.current = [];
      setIsDrawing(false);
    }
  };

  const handleUndo = () => {
    if (stamps.length > 0) {
      setStamps((prev) => prev.slice(0, -1));
    } else if (strokes.length > 0) {
      setStrokes((prev) => prev.slice(0, -1));
    }
  };

  const handleClear = () => {
    if (strokes.length === 0 && stamps.length === 0) return;
    const confirmed = typeof window !== 'undefined' && typeof window.confirm === 'function'
      ? window.confirm('Thầy cô có chắc chắn muốn xóa toàn bộ nét vẽ và tem chấm trên bài làm này?')
      : true;
    if (confirmed) {
      setStrokes([]);
      setStamps([]);
      currentStroke.current = [];
      saveSubmissionAnnotations(id, [], []);
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext ? canvas.getContext('2d') : null;
        ctx?.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  };

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
          onClick={handleRetry}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 1,
            px: 2.5,
            py: 1,
            bgcolor: '#059669',
            color: 'white',
            border: 'none',
            borderRadius: 1.5,
            fontWeight: 700,
            cursor: 'pointer',
            fontSize: '0.875rem',
            '&:hover': { bgcolor: '#047857' },
          }}
        >
          <RefreshIcon /> Thử lại tải ảnh
        </Box>
      </Box>
    );
  }

  if (effectiveError) {
    return (
      <Box sx={{ p: 3, maxWidth: 520, mx: 'auto', textAlign: 'center' }}>
        <Alert severity="error" sx={{ mb: 2, textAlign: 'left' }} role="alert">
          {effectiveError}
        </Alert>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          <Box
            component="button"
            onClick={handleRetry}
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
              fontWeight: 600,
              '&:hover': { borderColor: '#FFFFFF' },
            }}
          >
            <RefreshIcon /> Thử lại
          </Box>
          {src && (
            <Box
              component="a"
              href={src}
              download={`bai-lam-${studentName || id}.jpg`}
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 1,
                px: 2,
                py: 0.75,
                bgcolor: '#059669',
                color: 'white',
                textDecoration: 'none',
                borderRadius: 1.5,
                fontWeight: 600,
                fontSize: '0.85rem',
                '&:hover': { bgcolor: '#047857' },
              }}
            >
              Tải tệp ảnh gốc về máy
            </Box>
          )}
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
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
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
          zIndex: 15,
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
                bgcolor: '#059669',
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
            onClick={handleOpenFullscreen}
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

      {/* Image Display & Scroll Area */}
      <Box
        ref={containerRef}
        tabIndex={0}
        role="region"
        aria-label="Khung xem ảnh bài làm có thể cuộn"
        sx={{
          width: '100%',
          minHeight: { xs: 260, md: 540 },
          maxHeight: { xs: 460, md: 720 },
          overflow: 'auto',
          display: 'flex',
          bgcolor: '#0F172A',
          position: 'relative',
          p: 2,
          outline: 'none',
          userSelect: 'none',
          '&:focus-visible': {
            boxShadow: 'inset 0 0 0 2px #059669',
          },
        }}
      >
        <Box
          sx={{
            margin: 'auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth: 'min-content',
            minHeight: 'min-content',
            boxSizing: 'border-box',
          }}
        >
          <Box
            sx={{
              position: 'relative',
              width: fitToViewport ? 'auto' : `${boxWidth}px`,
              height: fitToViewport ? 'auto' : `${boxHeight}px`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'width 0.2s ease-out, height 0.2s ease-out',
            }}
            style={{
              width: fitToViewport ? undefined : `${boxWidth}px`,
              height: fitToViewport ? undefined : `${boxHeight}px`,
            }}
          >
            <Box
              component="img"
              src={src}
              alt={`Bài làm của ${studentName || 'học sinh'}`}
              onLoad={handleImageLoad}
              onError={handleImageError}
              sx={{
                maxWidth: fitToViewport ? '100%' : 'none',
                maxHeight: fitToViewport ? 650 : 'none',
                width: fitToViewport ? 'auto' : `${renderedWidth}px`,
                height: fitToViewport ? 'auto' : `${renderedHeight}px`,
                objectFit: 'contain',
                borderRadius: 1.5,
                transform: rotation !== 0 ? `rotate(${rotation}deg)` : undefined,
                transformOrigin: 'center center',
                transition: 'transform 0.2s ease-out, width 0.2s ease-out, height 0.2s ease-out',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.45)',
                display: 'block',
              }}
              style={{
                width: fitToViewport ? undefined : `${renderedWidth}px`,
                height: fitToViewport ? undefined : `${renderedHeight}px`,
                transform: rotation !== 0 ? `rotate(${rotation}deg)` : undefined,
              }}
            />

            {/* INTEGRATED ACCURATE GRADING CANVAS OVERLAY */}
            <canvas
              ref={canvasRef}
              onMouseDown={handlePointerDown}
              onMouseMove={handlePointerMove}
              onMouseUp={handlePointerUp}
              onTouchStart={handlePointerDown}
              onTouchMove={handlePointerMove}
              onTouchEnd={handlePointerUp}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                transform: rotation !== 0 ? `rotate(${rotation}deg)` : undefined,
                transformOrigin: 'center center',
                pointerEvents: showOverlay && activeTool ? 'auto' : 'none',
                cursor:
                  activeTool === 'pen' || activeTool === 'highlight'
                    ? 'crosshair'
                    : activeTool
                    ? 'pointer'
                    : 'default',
                zIndex: 10,
                touchAction: 'none',
                borderRadius: '6px',
              }}
            />
          </Box>
        </Box>
      </Box>

      {/* Floating Teacher Grading Tool Bar */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 14,
          left: '50%',
          transform: 'translateX(-50%)',
          bgcolor: 'rgba(15, 23, 42, 0.94)',
          backdropFilter: 'blur(10px)',
          borderRadius: 3,
          px: 1.25,
          py: 0.75,
          display: 'flex',
          alignItems: 'center',
          gap: 0.75,
          zIndex: 25,
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          border: '1px solid rgba(255, 255, 255, 0.18)',
        }}
      >
        {/* Tool: Pan / View mode */}
        <Box
          component="button"
          title="Chế độ xem & cuộn ảnh (Tắt vẽ)"
          aria-label="Chế độ xem ảnh"
          onClick={() => setActiveTool(null)}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 1.2,
            py: 0.5,
            fontSize: '0.8rem',
            fontWeight: 700,
            color: activeTool === null ? '#FFFFFF' : '#94A3B8',
            bgcolor: activeTool === null ? '#059669' : 'transparent',
            border: 'none',
            borderRadius: 1.5,
            cursor: 'pointer',
            '&:hover': { bgcolor: activeTool === null ? '#047857' : 'rgba(255,255,255,0.1)' },
          }}
        >
          ✋ Xem ảnh
        </Box>

        {/* Tool: Red Pen */}
        <Box
          component="button"
          title="Bút chấm đỏ (Vẽ tự do)"
          aria-label="Bút chấm đỏ"
          onClick={() => setActiveTool('pen')}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 1.2,
            py: 0.5,
            fontSize: '0.8rem',
            fontWeight: 700,
            color: activeTool === 'pen' ? '#FFFFFF' : '#EF4444',
            bgcolor: activeTool === 'pen' ? '#EF4444' : 'transparent',
            border: 'none',
            borderRadius: 1.5,
            cursor: 'pointer',
            '&:hover': { bgcolor: activeTool === 'pen' ? '#DC2626' : 'rgba(255,255,255,0.1)' },
          }}
        >
          ✏️ Bút đỏ
        </Box>

        {/* Tool: Highlighter */}
        <Box
          component="button"
          title="Bút dạ quang vàng (Gạch chân bước làm đúng)"
          aria-label="Bút dạ quang"
          onClick={() => setActiveTool('highlight')}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 1.2,
            py: 0.5,
            fontSize: '0.8rem',
            fontWeight: 700,
            color: activeTool === 'highlight' ? '#1E293B' : '#FBBF24',
            bgcolor: activeTool === 'highlight' ? '#FBBF24' : 'transparent',
            border: 'none',
            borderRadius: 1.5,
            cursor: 'pointer',
            '&:hover': { bgcolor: activeTool === 'highlight' ? '#F59E0B' : 'rgba(255,255,255,0.1)' },
          }}
        >
          ✨ Dạ quang
        </Box>

        {/* Tool: Checkmark */}
        <Box
          component="button"
          title="Đánh dấu Đúng (✓ Xanh)"
          aria-label="Dấu đúng"
          onClick={() => setActiveTool('check')}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 1,
            py: 0.5,
            fontSize: '0.9rem',
            fontWeight: 800,
            color: activeTool === 'check' ? '#FFFFFF' : '#10B981',
            bgcolor: activeTool === 'check' ? '#10B981' : 'transparent',
            border: 'none',
            borderRadius: 1.5,
            cursor: 'pointer',
            '&:hover': { bgcolor: activeTool === 'check' ? '#059669' : 'rgba(255,255,255,0.1)' },
          }}
        >
          ✓
        </Box>

        {/* Tool: Cross */}
        <Box
          component="button"
          title="Dấu Sai (✗ Đỏ)"
          aria-label="Dấu sai"
          onClick={() => setActiveTool('cross')}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 1,
            py: 0.5,
            fontSize: '0.9rem',
            fontWeight: 800,
            color: activeTool === 'cross' ? '#FFFFFF' : '#EF4444',
            bgcolor: activeTool === 'cross' ? '#EF4444' : 'transparent',
            border: 'none',
            borderRadius: 1.5,
            cursor: 'pointer',
            '&:hover': { bgcolor: activeTool === 'cross' ? '#DC2626' : 'rgba(255,255,255,0.1)' },
          }}
        >
          ✗
        </Box>

        {/* Tool: Circle */}
        <Box
          component="button"
          title="Khoanh tròn chỗ sai (⭕ Đỏ)"
          aria-label="Khoanh tròn"
          onClick={() => setActiveTool('circle')}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 1,
            py: 0.5,
            fontSize: '0.85rem',
            color: activeTool === 'circle' ? '#FFFFFF' : '#EF4444',
            bgcolor: activeTool === 'circle' ? '#EF4444' : 'transparent',
            border: 'none',
            borderRadius: 1.5,
            cursor: 'pointer',
            '&:hover': { bgcolor: activeTool === 'circle' ? '#DC2626' : 'rgba(255,255,255,0.1)' },
          }}
        >
          ⭕
        </Box>

        {/* Tool: Star */}
        <Box
          component="button"
          title="Tặng sao khen ngợi (⭐ Vàng)"
          aria-label="Khen thưởng"
          onClick={() => setActiveTool('star')}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 1,
            py: 0.5,
            fontSize: '0.85rem',
            color: activeTool === 'star' ? '#FFFFFF' : '#F59E0B',
            bgcolor: activeTool === 'star' ? '#F59E0B' : 'transparent',
            border: 'none',
            borderRadius: 1.5,
            cursor: 'pointer',
            '&:hover': { bgcolor: activeTool === 'star' ? '#D97706' : 'rgba(255,255,255,0.1)' },
          }}
        >
          ⭐
        </Box>

        <Box sx={{ width: 1, height: 20, bgcolor: 'rgba(255,255,255,0.2)', mx: 0.5 }} />

        {/* Undo */}
        <Box
          component="button"
          title="Hoàn tác nét vẽ gần nhất"
          aria-label="Hoàn tác"
          onClick={handleUndo}
          disabled={strokes.length === 0 && stamps.length === 0}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 0.5,
            color: '#CBD5E1',
            bgcolor: 'transparent',
            border: 'none',
            borderRadius: 1,
            cursor: strokes.length === 0 && stamps.length === 0 ? 'default' : 'pointer',
            opacity: strokes.length === 0 && stamps.length === 0 ? 0.35 : 1,
            fontSize: '0.85rem',
            '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
          }}
        >
          ↩️
        </Box>

        {/* Clear */}
        <Box
          component="button"
          title="Xóa toàn bộ đánh dấu trên ảnh"
          aria-label="Xóa tất cả"
          onClick={handleClear}
          disabled={strokes.length === 0 && stamps.length === 0}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 0.5,
            color: '#CBD5E1',
            bgcolor: 'transparent',
            border: 'none',
            borderRadius: 1,
            cursor: strokes.length === 0 && stamps.length === 0 ? 'default' : 'pointer',
            opacity: strokes.length === 0 && stamps.length === 0 ? 0.35 : 1,
            fontSize: '0.85rem',
            '&:hover': { bgcolor: 'rgba(239,68,68,0.2)', color: '#EF4444' },
          }}
        >
          🗑️
        </Box>

        {/* Visibility */}
        <Box
          component="button"
          title={showOverlay ? 'Ẩn toàn bộ nét chấm' : 'Hiện lại nét chấm'}
          aria-label="Ẩn hiện nét chấm"
          onClick={() => setShowOverlay(!showOverlay)}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 0.5,
            color: '#CBD5E1',
            bgcolor: 'transparent',
            border: 'none',
            borderRadius: 1,
            cursor: 'pointer',
            fontSize: '0.85rem',
            '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
          }}
        >
          {showOverlay ? '👁️' : '🙈'}
        </Box>
      </Box>

      {/* Accessible Fullscreen Modal for Detailed Inspection */}
      {fullscreenOpen && (
        <Box
          ref={fullscreenModalRef}
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
                ref={closeButtonRef}
                component="button"
                aria-label="Đóng chế độ xem toàn màn hình"
                onClick={handleCloseFullscreen}
                sx={{ color: '#CBD5E1', bgcolor: 'transparent', border: 'none', p: 0.5, cursor: 'pointer', ml: 1 }}
              >
                <CloseIcon />
              </Box>
            </Box>
          </Box>

          {/* Modal Content */}
          <Box
            tabIndex={0}
            role="region"
            aria-label="Khu vực cuộn ảnh chi tiết"
            sx={{
              flex: 1,
              bgcolor: '#0B0F19',
              display: 'flex',
              p: 2,
              overflow: 'auto',
              outline: 'none',
            }}
          >
            <Box
              sx={{
                margin: 'auto',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: 'min-content',
                minHeight: 'min-content',
              }}
            >
              <Box
                component="img"
                src={src}
                alt={`Chi tiết bài làm của ${studentName || 'học sinh'}`}
                sx={{
                  maxWidth: 'none',
                  maxHeight: 'none',
                  width: `${renderedWidth}px`,
                  height: `${renderedHeight}px`,
                  objectFit: 'contain',
                  borderRadius: 1.5,
                  transform: rotation !== 0 ? `rotate(${rotation}deg)` : undefined,
                  transformOrigin: 'center center',
                  transition: 'transform 0.2s ease-out, width 0.2s ease-out, height 0.2s ease-out',
                }}
              />
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}

export default SubmissionImage;

