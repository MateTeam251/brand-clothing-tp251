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
  first_name: string;
  last_name: string;
  birth_date: string | null;
  phone_number: string;
  marketing_opt_in: boolean;
  instagram: string;
  telegram: string;
}