import { useRef, useState } from 'react';
import type { TouchEvent } from 'react';

const CLOSE_THRESHOLD = 100;

export function useSwipeToClose(onClose: () => void) {
  const [dragOffset, setDragOffset] = useState(0);
  const startY = useRef<number | null>(null);
  const isDragging = useRef(false);

  const handleTouchStart = (event: TouchEvent<HTMLDivElement>) => {
    startY.current = event.touches[0].clientY;
    isDragging.current = true;
  };

  const handleTouchMove = (event: TouchEvent<HTMLDivElement>) => {
    if (!isDragging.current || startY.current === null) {
      return;
    }

    const currentY = event.touches[0].clientY;
    const diff = currentY - startY.current;

    if (diff > 0) {
      setDragOffset(diff);
    }
  };

  const handleTouchEnd = () => {
    if (dragOffset > CLOSE_THRESHOLD) {
      onClose();
    }

    setDragOffset(0);
    isDragging.current = false;
    startY.current = null;
  };

  return {
    dragOffset,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
  };
}