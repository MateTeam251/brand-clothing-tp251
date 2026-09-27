export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const SIZES = ['2XS', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL'] as const;
export type Size = (typeof SIZES)[number];