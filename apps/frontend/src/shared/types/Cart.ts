import type { Size } from './common';
import type { ProductImage } from './products';

export interface CartLine {
  id: number;
  product: number;
  name: string;
  main_image: ProductImage | null;
  size: string | Size;
  quantity: number;
  price: string;
  total_full_price: string;
  total_price: string;
  is_available: boolean;
  is_archived: boolean;
}

export interface Cart {
  id: number;
  status: string;
  items: CartLine[];
  items_count: number;
  items_total: string;
}

export interface AddCartItemBody {
  product: number;
  size: string | Size;
  quantity?: number;
}

export interface CartQueryArg {
  currency: string;
  isAuthenticated: boolean;
}