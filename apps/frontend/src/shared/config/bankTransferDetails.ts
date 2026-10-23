import type { Currency } from '../types/orders';

export interface BankTransferDetailsData {
  recipient: string;
  iban: string;
  bank: string;
  taxId: string;
  swift?: string;
}

// TODO: заповнити реквізитами від замовниці.
// Поки null: блок «Оплатити за реквізитами» на сайті не показується.
export const BANK_TRANSFER_DETAILS: Record<Currency, BankTransferDetailsData | null> = {
  UAH: null,
  USD: null,
};

// Показується тільки в режимі розробки (npm run dev), щоб бачити вигляд блока.
export const DEV_PLACEHOLDER_DETAILS: BankTransferDetailsData = {
  recipient: 'ТЕСТ: ФОП Прізвище І. Б.',
  iban: 'UA00 0000 0000 0000 0000 0000 00000',
  bank: 'ТЕСТ: Назва банку',
  taxId: '0000000000',
  swift: 'TESTUA00',
};