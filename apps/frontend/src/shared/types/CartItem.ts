import type { ProductImage } from './products';
import type { Size } from './common';

export interface CartItem {
  id: number;
  product: number;
  name: string;
  main_image: ProductImage | null;
  size: Size;
  quantity: number;
  price: string;
  total_price: string;
}