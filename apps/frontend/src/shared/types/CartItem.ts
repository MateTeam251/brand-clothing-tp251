import type { Size } from './common';

export interface CartItem {
  id: number; 
  product: number;    
  size: string | Size; 
  quantity: number;    
}