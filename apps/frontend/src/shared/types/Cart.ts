import type { CartItem } from './CartItem';

export type Cart = {
  id: number;
  status: string;
  items: CartItem[];
  items_count: number;
  items_total: string;
}