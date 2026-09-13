export type PaymentStatus = 'PENDING' | 'SUCCESSFUL' | 'FAILED';  // need confirmation by backend
export type PaymentProvider = 'WAYFORPAY';

export interface Payment {
  id: number;
  order: number;
  currency: string;
  amount: string;
  provider: PaymentProvider;
  status: PaymentStatus;
  transaction_id: string;
  payment_data: Record<string, unknown>;  //unknown fields, need confirmation
  paid_at: string | null;
  created_at: string;
  updated_at: string;
}