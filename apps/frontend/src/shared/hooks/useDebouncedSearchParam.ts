import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useDebounce } from './useDebounce';

export function useDebouncedSearchParam(paramName: string, delay = 500) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [inputValue, setInputValue] = useState(() => searchParams.get(paramName) ?? '');
  const debouncedValue = useDebounce(inputValue, delay);

  const [lastSyncedValue, setLastSyncedValue] = useState(debouncedValue);

  if (debouncedValue !== lastSyncedValue) {
    setLastSyncedValue(debouncedValue);
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (debouncedValue) {
          next.set(paramName, debouncedValue);
        } else {
          next.delete(paramName);
        }
        return next;
      },
      { replace: true },
    );
  }

  return [inputValue, setInputValue] as const;
}