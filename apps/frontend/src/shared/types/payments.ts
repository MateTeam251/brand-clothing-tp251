export type PaymentStatus = 'PENDING' | 'SUCCESSFUL' | 'FAILED' | 'REFUNDED';
export type PaymentProvider = 'WAYFORPAY';

export interface PaymentData {
  reason_code: number;
  transaction_status: string;
  payment_system: string;
}

export interface Payment {
  id: number;
  order: number;
  currency: string;
  amount: string;
  provider: PaymentProvider;
  status: PaymentStatus;
  transaction_id: string;
  payment_data: PaymentData;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
}