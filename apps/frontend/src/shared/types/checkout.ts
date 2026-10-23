export interface CheckoutContactValues {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
}

export type CheckoutContactErrors = Partial<Record<keyof CheckoutContactValues, string>>;
