import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent as ReactKeyboardEvent } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Box, IconButton, Tooltip, Typography } from '@mui/material';
import { Close, Brush, ClearAll, Save, Delete as DeleteIcon } from '@mui/icons-material';

interface PrivacyEditorModalProps {
  open: boolean;
  onClose: () => void;
  file: File | null;
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
  const [initialMaskState, setInitialMaskState] = useState<Mask | null>(null);

  useEffect(() => {
    if (open && file) {
      setMasks([]);
      setSelectedMask(null);
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        setImageObj(img);
        URL.revokeObjectURL(url);
      };
      img.src = url;
    } else {
      setImageObj(null);
    }
  }, [open, file]);

  const drawCanvas = () => {
    if (!imageObj || !canvasRef.current || !containerRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const container = containerRef.current;
    const maxWidth = container.clientWidth;
    const maxHeight = window.innerHeight * 0.6;

    let newScale = 1;
    if (imageObj.width > maxWidth || imageObj.height > maxHeight) {
      newScale = Math.min(maxWidth / imageObj.width, maxHeight / imageObj.height);
    }
    setScale(newScale);

    canvas.width = imageObj.width * newScale;
    canvas.height = imageObj.height * newScale;

    ctx.drawImage(imageObj, 0, 0, canvas.width, canvas.height);

    masks.forEach(m => {
      ctx.fillStyle = m.id === selectedMask ? 'rgba(0, 0, 0, 0.8)' : 'black';
      ctx.fillRect(m.x, m.y, m.width, m.height);
      
      if (m.id === selectedMask) {
        ctx.strokeStyle = '#1976d2';
        ctx.lineWidth = 2;
        ctx.strokeRect(m.x, m.y, m.width, m.height);
        
        // Handles
        ctx.fillStyle = 'white';
        const hSize = 6;
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
  }, [imageObj, masks, isDrawing, currentPos, startPos, selectedMask, scale]);

  const getMousePos = (evt: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: evt.clientX - rect.left,
      y: evt.clientY - rect.top
    };
  };

  const getResizeEdge = (pos: {x: number, y: number}, m: Mask) => {
    const margin = 8;
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

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
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

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
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
      handleDeleteSelected();
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
    if (!imageObj || !file) return;

    const offscreen = document.createElement('canvas');
    offscreen.width = imageObj.width;
    offscreen.height = imageObj.height;
    const ctx = offscreen.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(imageObj, 0, 0);
    ctx.fillStyle = 'black';

    const scaleX = imageObj.width / (canvasRef.current?.width || imageObj.width);
    const scaleY = imageObj.height / (canvasRef.current?.height || imageObj.height);

    masks.forEach(m => {
      ctx.fillRect(m.x * scaleX, m.y * scaleY, m.width * scaleX, m.height * scaleY);
    });

    offscreen.toBlob((blob) => {
      if (blob) onSave(blob);
    }, file.type || 'image/jpeg', 0.9);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Che thông tin cá nhân (Privacy Gate)</Typography>
        <IconButton onClick={onClose}><Close /></IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary">
            <Brush fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
            Kéo chuột để vẽ, click để chọn, kéo viền để sửa, hoặc xóa vùng che.
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Tooltip title="Xóa vùng đang chọn">
            <span>
              <IconButton onClick={handleDeleteSelected} disabled={!selectedMask} color="error"><DeleteIcon /></IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Xóa tất cả">
            <span>
              <IconButton onClick={handleClear} disabled={masks.length === 0}><ClearAll /></IconButton>
            </span>
          </Tooltip>
        </Box>
        <Box 
          ref={containerRef} 
          sx={{ display: 'flex', justifyContent: 'center', bgcolor: 'grey.100', p: 2, borderRadius: 1, minHeight: 300 }}
          onKeyDown={handleKeyDown}
          tabIndex={0}
        >
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', outline: 'none' }}
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} color="inherit">Hủy</Button>
        <Button onClick={handleSave} variant="contained" startIcon={<Save />}>
          Lưu ảnh đã che
        </Button>
      </DialogActions>
    </Dialog>
  );
}
