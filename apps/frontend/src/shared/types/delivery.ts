export type DeliveryProvider = 'NOVA_POSHTA' | 'UKRPOSHTA' | 'DHL';

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