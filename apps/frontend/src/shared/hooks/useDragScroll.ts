import { useRef } from 'react';
import type { PointerEvent as ReactPointerEvent, MouseEvent as ReactMouseEvent } from 'react';

export function useDragScroll<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const dragStartX = useRef(0);
  const dragStartScrollLeft = useRef(0);
  const isDragging = useRef(false);
  const hasDragged = useRef(false);

  const handlePointerDown = (event: ReactPointerEvent<T>) => {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    const el = ref.current;
    if (!el || el.scrollWidth <= el.clientWidth) return;

    isDragging.current = true;
    hasDragged.current = false;
    dragStartX.current = event.clientX;
    dragStartScrollLeft.current = el.scrollLeft;
    el.setPointerCapture(event.pointerId);
    el.classList.add('is-dragging');
  };

  const handlePointerMove = (event: ReactPointerEvent<T>) => {
    if (!isDragging.current || !ref.current) return;
    const distance = event.clientX - dragStartX.current;
    if (Math.abs(distance) > 5) hasDragged.current = true;
    ref.current.scrollLeft = dragStartScrollLeft.current - distance;
  };

  const handlePointerUp = (event: ReactPointerEvent<T>) => {
    const el = ref.current;
    if (!el || !isDragging.current) return;
    isDragging.current = false;
    el.releasePointerCapture(event.pointerId);
    el.classList.remove('is-dragging');
  };

  const handleClickCapture = (event: ReactMouseEvent<T>) => {
    if (hasDragged.current) {
      event.preventDefault();
      event.stopPropagation();
      hasDragged.current = false;
    }
  };

  return { ref, handlePointerDown, handlePointerMove, handlePointerUp, handleClickCapture };
}