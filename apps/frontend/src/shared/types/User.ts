import type { DeliveryProvider } from "./delivery";

export interface Address {
  country: string;
  full_name: string;
  phone_number: string;
  region: string;
  city: string;
  postal_code: string;
  address_line_1: string;
  address_line_2: string;
  delivery_provider: DeliveryProvider;
  delivery_point: string;
}

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  age: number;
  phone_number: string;
  marketing_opt_in: boolean;
  instagram: string;
  address: Address;
}