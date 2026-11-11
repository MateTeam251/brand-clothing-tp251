export type DeliveryProvider = 'NOVA_POSHTA' | 'NOVA_POST';

export interface NovaPostCountry {
  code: string;
  name_ua: string;
  name_en: string;
}

export interface DeliveryCity {
  id: number;
  provider: DeliveryProvider;
  country: string;
  name: string;
}

export interface DeliveryBranch {
  id: number;
  provider: DeliveryProvider;
  city: number;
  name: string;
  address: string;
  postal_code: string;
}

export const CHECKOUT_DELIVERY_PROVIDER: DeliveryProvider = 'NOVA_POSHTA';
export const INTERNATIONAL_DELIVERY_PROVIDER: DeliveryProvider = 'NOVA_POST';