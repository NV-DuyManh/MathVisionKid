/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent as ReactKeyboardEvent } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Box, IconButton, Tooltip, Typography, Alert } from '@mui/material';
import { Close, Brush, ClearAll, Save, Delete as DeleteIcon } from '@mui/icons-material';

interface PrivacyEditorModalProps {
  open: boolean;
  onClose: () => void;
  file: Blob | null;
  onSave: (sanitizedBlob: Blob) => void;
}

interface Mask {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export default function PrivacyEditorModal({ open, onClose, file, onSave }: PrivacyEditorModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [masks, setMasks] = useState<Mask[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isMoving, setIsMoving] = useState<string | null>(null);
  const [isResizing, setIsResizing] = useState<string | null>(null);
  const [resizeEdge, setResizeEdge] = useState<string | null>(null); // 'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'
  const [selectedMask, setSelectedMask] = useState<string | null>(null);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [currentPos, setCurrentPos] = useState({ x: 0, y: 0 });
  const [imageObj, setImageObj] = useState<HTMLImageElement | null>(null);
  const [scale, setScale] = useState(1);
  const [imageError, setImageError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [initialMaskState, setInitialMaskState] = useState<Mask | null>(null);

  useEffect(() => {
    setMasks([]);
    setSelectedMask(null);
    setImageObj(null);
    setImageError(null);
    setSaving(false);
    setIsDrawing(false);
    setIsMoving(null);
    setIsResizing(null);
    if (!open || !file) return;
    let active = true;
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => { if (active) setImageObj(img); };
    img.onerror = () => { if (active) setImageError('Chưa mở được ảnh. Hãy chọn ảnh JPG, PNG hoặc WebP rõ nét.'); };
    img.src = url;
    return () => { active = false; URL.revokeObjectURL(url); };
  }, [open, file]);

  const drawCanvas = () => {
    if (!imageObj || !canvasRef.current || !containerRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const container = containerRef.current;
    const maxWidth = Math.max(1, container.clientWidth - 32);
    const maxHeight = window.innerHeight * 0.6;

    let newScale = 1;
    if (imageObj.width > maxWidth || imageObj.height > maxHeight) {
      newScale = Math.min(maxWidth / imageObj.width, maxHeight / imageObj.height);
    }
    setScale(newScale);

    canvas.width = imageObj.width * newScale;
    canvas.height = imageObj.height * newScale;

    // Store masks in original-image coordinates so resizing never moves a privacy mask.
    ctx.setTransform(newScale, 0, 0, newScale, 0, 0);
    ctx.drawImage(imageObj, 0, 0);

    masks.forEach(m => {
      ctx.fillStyle = m.id === selectedMask ? 'rgba(0, 0, 0, 0.8)' : 'black';
      ctx.fillRect(m.x, m.y, m.width, m.height);
      
      if (m.id === selectedMask) {
        ctx.strokeStyle = '#1976d2';
        ctx.lineWidth = 2 / newScale;
        ctx.strokeRect(m.x, m.y, m.width, m.height);
        
        // Handles
        ctx.fillStyle = 'white';
        const hSize = 6 / newScale;
        const handles = [
          { x: m.x - hSize/2, y: m.y - hSize/2 }, // nw
          { x: m.x + m.width/2 - hSize/2, y: m.y - hSize/2 }, // n
          { x: m.x + m.width - hSize/2, y: m.y - hSize/2 }, // ne
          { x: m.x + m.width - hSize/2, y: m.y + m.height/2 - hSize/2 }, // e
          { x: m.x + m.width - hSize/2, y: m.y + m.height - hSize/2 }, // se
          { x: m.x + m.width/2 - hSize/2, y: m.y + m.height - hSize/2 }, // s
          { x: m.x - hSize/2, y: m.y + m.height - hSize/2 }, // sw
          { x: m.x - hSize/2, y: m.y + m.height/2 - hSize/2 }, // w
        ];
        handles.forEach(h => {
          ctx.strokeRect(h.x, h.y, hSize, hSize);
          ctx.fillRect(h.x, h.y, hSize, hSize);
        });
      }
    });

    if (isDrawing) {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
      const width = currentPos.x - startPos.x;
      const height = currentPos.y - startPos.y;
      ctx.fillRect(startPos.x, startPos.y, width, height);
    }
  };

  useEffect(() => {
    drawCanvas();
    const observer = new ResizeObserver(drawCanvas);
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [imageObj, masks, isDrawing, currentPos, startPos, selectedMask, scale]);

  const getMousePos = (evt: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(imageObj?.width || 0, (evt.clientX - rect.left) / scale)),
      y: Math.max(0, Math.min(imageObj?.height || 0, (evt.clientY - rect.top) / scale))
    };
  };

  const getResizeEdge = (pos: {x: number, y: number}, m: Mask) => {
    const margin = 8 / scale;
    if (pos.x < m.x - margin || pos.x > m.x + m.width + margin ||
        pos.y < m.y - margin || pos.y > m.y + m.height + margin) return null;
    const isLeft = Math.abs(pos.x - m.x) < margin;
    const isRight = Math.abs(pos.x - (m.x + m.width)) < margin;
    const isTop = Math.abs(pos.y - m.y) < margin;
    const isBottom = Math.abs(pos.y - (m.y + m.height)) < margin;
    
    if (isTop && isLeft) return 'nw';
    if (isTop && isRight) return 'ne';
    if (isBottom && isLeft) return 'sw';
    if (isBottom && isRight) return 'se';
    if (isTop) return 'n';
    if (isBottom) return 's';
    if (isLeft) return 'w';
    if (isRight) return 'e';
    return null;
  };

  const handleMouseDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!imageObj || saving) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    const pos = getMousePos(e);
    
    // Check if clicked on selected mask handle for resize
    if (selectedMask) {
      const m = masks.find(x => x.id === selectedMask);
      if (m) {
        const edge = getResizeEdge(pos, m);
        if (edge) {
          setIsResizing(m.id);
          setResizeEdge(edge);
          setInitialMaskState({...m});
          setStartPos(pos);
          return;
        }
      }
    }

    // Check if clicked inside a mask to move or select
    for (let i = masks.length - 1; i >= 0; i--) {
      const m = masks[i];
      if (pos.x >= m.x && pos.x <= m.x + m.width && pos.y >= m.y && pos.y <= m.y + m.height) {
        setSelectedMask(m.id);
        setIsMoving(m.id);
        setInitialMaskState({...m});
        setStartPos(pos);
        return;
      }
    }

    // Otherwise start drawing new mask
    setSelectedMask(null);
    setStartPos(pos);
    setCurrentPos(pos);
    setIsDrawing(true);
  };

  const handleMouseMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const pos = getMousePos(e);
    
    // Update cursor
    if (canvasRef.current) {
      let cursor = 'crosshair';
      if (selectedMask) {
        const m = masks.find(x => x.id === selectedMask);
        if (m) {
          const edge = getResizeEdge(pos, m);
          if (edge === 'nw' || edge === 'se') cursor = 'nwse-resize';
          else if (edge === 'ne' || edge === 'sw') cursor = 'nesw-resize';
          else if (edge === 'n' || edge === 's') cursor = 'ns-resize';
          else if (edge === 'e' || edge === 'w') cursor = 'ew-resize';
          else if (pos.x >= m.x && pos.x <= m.x + m.width && pos.y >= m.y && pos.y <= m.y + m.height) cursor = 'move';
        }
      }
      canvasRef.current.style.cursor = cursor;
    }

    if (isDrawing) {
      setCurrentPos(pos);
    } else if (isMoving && initialMaskState) {
      const dx = pos.x - startPos.x;
      const dy = pos.y - startPos.y;
      setMasks(prev => prev.map(m => m.id === isMoving ? {
        ...m,
        x: initialMaskState.x + dx,
        y: initialMaskState.y + dy
      } : m));
    } else if (isResizing && initialMaskState && resizeEdge) {
      const dx = pos.x - startPos.x;
      const dy = pos.y - startPos.y;
      setMasks(prev => prev.map(m => {
        if (m.id !== isResizing) return m;
        const updated = { ...initialMaskState };
        if (resizeEdge.includes('w')) { updated.x += dx; updated.width -= dx; }
        if (resizeEdge.includes('e')) { updated.width += dx; }
        if (resizeEdge.includes('n')) { updated.y += dy; updated.height -= dy; }
        if (resizeEdge.includes('s')) { updated.height += dy; }
        return updated;
      }));
    }
  };

  const handleMouseUp = () => {
    if (isDrawing) {
      setIsDrawing(false);
      const width = currentPos.x - startPos.x;
      const height = currentPos.y - startPos.y;
      if (Math.abs(width) > 10 && Math.abs(height) > 10) {
        const newMask = {
          id: Math.random().toString(36).substring(2, 9),
          x: width > 0 ? startPos.x : currentPos.x,
          y: height > 0 ? startPos.y : currentPos.y,
          width: Math.abs(width),
          height: Math.abs(height)
        };
        setMasks([...masks, newMask]);
        setSelectedMask(newMask.id);
      }
    }
    
    // Normalize negative widths/heights after resize
    if (isResizing) {
      setMasks(prev => prev.map(m => {
        if (m.id !== isResizing) return m;
        let { x, y, width, height } = m;
        if (width < 0) { x += width; width = Math.abs(width); }
        if (height < 0) { y += height; height = Math.abs(height); }
        return { ...m, x, y, width, height };
      }));
    }

    setIsMoving(null);
    setIsResizing(null);
    setInitialMaskState(null);
    setResizeEdge(null);
  };

  const handleKeyDown = (e: ReactKeyboardEvent) => {
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedMask) {
      e.preventDefault();
      handleDeleteSelected();
    }
    const delta = ({ ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] } as Record<string, number[]>)[e.key];
    if (delta && selectedMask && imageObj) {
      e.preventDefault();
      const step = (e.shiftKey ? 10 : 1) / scale;
      setMasks(prev => prev.map(m => m.id === selectedMask ? { ...m,
        x: Math.max(0, Math.min(imageObj.width - m.width, m.x + delta[0] * step)),
        y: Math.max(0, Math.min(imageObj.height - m.height, m.y + delta[1] * step)),
      } : m));
    }
  };

  const handleDeleteSelected = () => {
    if (selectedMask) {
      setMasks(prev => prev.filter(m => m.id !== selectedMask));
      setSelectedMask(null);
    }
  };

  const handleClear = () => {
    setMasks([]);
    setSelectedMask(null);
  };

  const handleSave = () => {
    if (!imageObj || !file || saving || isDrawing || isMoving || isResizing) return;

    const offscreen = document.createElement('canvas');
    offscreen.width = imageObj.width;
    offscreen.height = imageObj.height;
    const ctx = offscreen.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, offscreen.width, offscreen.height);
    ctx.drawImage(imageObj, 0, 0);
    ctx.fillStyle = 'black';

    masks.forEach(m => ctx.fillRect(m.x, m.y, m.width, m.height));
    setSaving(true);
    offscreen.toBlob((blob) => {
      setSaving(false);
      if (blob) onSave(blob);
      else setImageError('Chưa lưu được ảnh. Hãy thử lại.');
    }, 'image/jpeg', 0.95);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth aria-labelledby="privacy-editor-title">
      <DialogTitle id="privacy-editor-title" sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography component="span" variant="h6">Che thông tin cá nhân</Typography>
        <IconButton aria-label="Đóng trình che thông tin" onClick={onClose}><Close /></IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary">
            <Brush fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
            Kéo để vẽ vùng che. Chọn một vùng để di chuyển hoặc sửa kích thước. Dùng phím mũi tên để di chuyển, Delete để xóa.
          </Typography>
          <Button disabled={!imageObj || saving} onClick={() => {
            if (!imageObj) return;
            const mask = { id: crypto.randomUUID(), x: 0, y: 0, width: imageObj.width * 0.4, height: imageObj.height * 0.1 };
            setMasks(prev => [...prev, mask]); setSelectedMask(mask.id);
            containerRef.current?.focus();
          }}>Thêm vùng che</Button>
          <Box sx={{ flexGrow: 1 }} />
          <Tooltip title="Xóa vùng đang chọn">
            <span>
              <IconButton aria-label="Xóa vùng đang chọn" onClick={handleDeleteSelected} disabled={!selectedMask} color="error"><DeleteIcon /></IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Xóa tất cả">
            <span>
              <IconButton aria-label="Xóa tất cả vùng che" onClick={handleClear} disabled={masks.length === 0}><ClearAll /></IconButton>
            </span>
          </Tooltip>
        </Box>
        {imageError && <Alert severity="error" sx={{ mb: 2 }}>{imageError}</Alert>}
        {!imageObj && !imageError && <Typography role="status">Đang mở ảnh…</Typography>}
        <Box
          aria-label="Vùng chỉnh sửa ảnh, dùng phím mũi tên để di chuyển vùng che đã chọn"
          ref={containerRef} 
          sx={{ display: 'flex', justifyContent: 'center', bgcolor: 'grey.100', p: 2, borderRadius: 1, minHeight: 300 }}
          onKeyDown={handleKeyDown}
          tabIndex={0}
        >
          <canvas
            ref={canvasRef}
            onPointerDown={handleMouseDown}
            onPointerMove={handleMouseMove}
            onPointerUp={handleMouseUp}
            onPointerCancel={handleMouseUp}
            aria-label="Ảnh cần che thông tin"
            style={{ touchAction: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', outline: 'none' }}
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} color="inherit">Hủy</Button>
        <Button disabled={!imageObj || saving || isDrawing || Boolean(isMoving) || Boolean(isResizing)} onClick={handleSave} variant="contained" startIcon={<Save />}>
          {saving ? 'Đang lưu…' : 'Lưu ảnh đã che'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
