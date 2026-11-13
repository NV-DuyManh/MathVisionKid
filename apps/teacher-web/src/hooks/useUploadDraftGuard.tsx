import { useRef } from 'react';
import { useBlocker } from 'react-router-dom';
import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from '@mui/material';

export function useUploadDraftGuard(active: boolean, onDiscard: () => void) {
  const allowNext = useRef(false);
  const blocker = useBlocker(({ currentLocation, nextLocation, historyAction }) => {
    if (historyAction === 'REPLACE' && nextLocation.pathname === '/login') return false;
    if (allowNext.current) {
      allowNext.current = false;
      return false;
    }
    return active && (currentLocation.pathname !== nextLocation.pathname
      || currentLocation.search !== nextLocation.search
      || currentLocation.state?.assignmentId !== nextLocation.state?.assignmentId);
  });

  const confirmation = (
    <Dialog open={blocker.state === 'blocked'} onClose={() => blocker.reset?.()}
      aria-labelledby="upload-draft-dialog-title" aria-describedby="upload-draft-dialog-description">
      <DialogTitle id="upload-draft-dialog-title">Rời trang tải ảnh?</DialogTitle>
      <DialogContent>
        <DialogContentText id="upload-draft-dialog-description">
          Ảnh chưa gửi sẽ bị mất khi rời trang. Lần gửi đã bắt đầu có thể tiếp tục xử lý.
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button autoFocus onClick={() => blocker.reset?.()}>Ở lại</Button>
        <Button onClick={() => {
          if (blocker.state === 'blocked') {
            onDiscard();
            blocker.proceed();
          }
        }}>Rời trang</Button>
      </DialogActions>
    </Dialog>
  );

  return { confirmation, allowNextNavigation: () => { allowNext.current = true; } };
}
