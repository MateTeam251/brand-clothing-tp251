import type { DeliveryProvider } from "./delivery";


export type OrderStatus = 'CREATED' | 'PAID' | 'SHIPPED' | 'DELIVERED';  // need to comfirm by backend
export type Currency = 'UAH' | 'USD';
export type Size = 'XS' | 'S' | 'M' | 'L' | 'XL';  // need to comfirm by backend

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
  delivery_cost: string;
  total_amount: string;
  delivery_provider: DeliveryProvider;
  delivery_data: string;
  items: OrderItem[];
}