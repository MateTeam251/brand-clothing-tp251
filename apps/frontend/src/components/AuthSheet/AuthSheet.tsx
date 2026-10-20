import { useEffect, useRef } from 'react';
import type { MouseEvent, PointerEvent, ReactNode } from 'react';
import { useSwipeToClose } from '../../shared/hooks/useSwipeToClose';
import styles from './AuthSheet.module.scss';

interface AuthSheetProps {
  children: ReactNode;
  onClose: () => void;
}

export const AuthSheet = ({ children, onClose }: AuthSheetProps) => {
  const { dragOffset, handleTouchStart, handleTouchMove, handleTouchEnd } =
    useSwipeToClose(onClose);
  const pressStartedOnOverlay = useRef(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleOverlayPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    pressStartedOnOverlay.current = event.target === event.currentTarget;
  };

  const handleOverlayClick = (event: MouseEvent<HTMLDivElement>) => {
    const startedOnOverlay = pressStartedOnOverlay.current;
    pressStartedOnOverlay.current = false;

    if (startedOnOverlay && event.target === event.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className={styles.overlay}
      onPointerDown={handleOverlayPointerDown}
      onClick={handleOverlayClick}
    >
      <div
        className={styles.sheet}
        style={
          dragOffset > 0
            ? { transform: `translateY(${dragOffset}px)`, transition: 'none' }
            : undefined
        }
      >
        <div
          className={styles.sheet__handle}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <span className={styles.sheet__handleBar} />
        </div>
        {children}
      </div>
    </div>
  );
};