import type { DeliveryProvider } from './delivery';
import type { Size } from './common';

export type OrderStatus =
  | 'PENDING'
  | 'PAID'
  | 'AWAITING_SHIPMENT'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'CANCELED';

export type Currency = 'UAH' | 'USD';

export interface OrderItem {
  id: number;
  product: number;
  product_name: string;
  size: Size;
  quantity: number;
  fabric_composition_ua: string;
  fabric_composition_eng: string;
  price_at_purchase: string;
  discount_percent_at_purchase: number;
  line_total: string;
}

export interface Order {
  id: number;
  user_name: string;
  user_phone: string;
  email: string;
  delivery_address: string;
  created_at: string;
  status: OrderStatus;
  currency: Currency;
  subtotal: string;
  discount_amount: string;
  total_amount: string;
  delivery_provider: DeliveryProvider;
  delivery_data: string;
  items: OrderItem[];
}