import type { Cart } from './Cart';
import type { Product } from './Product';
import type { Fabric } from './Fabric';

export interface CartItem {
  id: number;
  cart: Cart;
  product: Product;
  quantity: number;
  fabric: Fabric;
}