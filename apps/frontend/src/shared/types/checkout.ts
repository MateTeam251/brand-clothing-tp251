import type { DeliveryBranch, DeliveryCity, DeliveryProvider } from './delivery';
import type { Currency } from './orders';
export interface CheckoutContactValues {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
}

export type CheckoutContactErrors = Partial<Record<keyof CheckoutContactValues, string>>;

export type DeliveryMode = 'ukraine' | 'international';

export interface InternationalDeliveryValues {
  country: string;
  countryName: string;
  city: string;
  address: string;
  postalCode: string;
}

export interface CheckoutDeliveryValues {
  mode: DeliveryMode;
  city: DeliveryCity | null;
  branch: DeliveryBranch | null;
  international: InternationalDeliveryValues;
}

export interface CheckoutDeliveryErrors {
  city?: string;
  branch?: string;
  country?: string;
  internationalCity?: string;
  address?: string;
  postalCode?: string;
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
  order_reference: string;
  payment_id: number;
  payment_url: string;
}