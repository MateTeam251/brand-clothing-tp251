import type { Size } from './common';

export interface CartElement {
  id: number; 
  product: number;    
  size: string | Size; 
  quantity: number;    
}

export type Cart = {
  id: number;
  status: string;
  items: CartElement[];
  items_count: number;
  items_total: string;
}