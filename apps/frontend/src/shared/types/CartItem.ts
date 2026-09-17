import type { Cart } from './Cart';
import type { Product } from './Product';
import type { Fabric } from './Fabric';

export const SizeEnum = {
  XS: 'XS',
  S: 'S',
  M: 'M',
  L: 'L',
  XL: 'XL',
} as const;

export type SizeEnum = typeof SizeEnum[keyof typeof SizeEnum];

export interface CartItem {
  id: number;
  cart: Cart;
  product: Product;
  quantity: number;
  size: SizeEnum;
  fabric: Fabric;
}