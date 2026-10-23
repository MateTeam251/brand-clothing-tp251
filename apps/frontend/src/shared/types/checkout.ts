import type { DeliveryBranch, DeliveryCity, DeliveryProvider } from './delivery';
import type { Currency } from './orders';
export interface CheckoutContactValues {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
}

export type CheckoutContactErrors = Partial<Record<keyof CheckoutContactValues, string>>;

export interface CheckoutDeliveryValues {
  city: DeliveryCity | null;
  branch: DeliveryBranch | null;
}

export interface CheckoutDeliveryErrors {
  city?: string;
  branch?: string;
}

export interface CheckoutRequest {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  currency: Currency;
  delivery_provider: DeliveryProvider;
  delivery_address: string;
  delivery_data: Record<string, unknown>;
}

export interface CheckoutResponse {
  order_id: number;
  payment_id: number;
  payment_url: string;
}