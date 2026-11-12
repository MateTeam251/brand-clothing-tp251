import type { Currency } from '../types/orders';

export interface BankTransferDetailsData {
  recipient: string;
  iban: string;
  bank: string;
  taxId: string;
  swift?: string;
  // Якщо задано, призначення платежу береться звідси (для валютних переказів: англійською).
  purpose?: { default: string; withId: string };
}

// Реквізити по валютах. null: для цієї валюти оплата за реквізитами недоступна.
export const BANK_TRANSFER_DETAILS: Record<Currency, BankTransferDetailsData | null> = {
  UAH: {
    recipient: "ФОП Кириченко Дар'я Володимирівна",
    iban: 'UA58 305299 00000 26004026230637',
    bank: 'АТ КБ "ПРИВАТБАНК"',
    taxId: '3477605484',
  },
  USD: {
    recipient: 'FOP Kyrychenko Daria Volodymyrivna',
    iban: 'UA81 3052 9900 0002 6008 0162 5538 3',
    bank: 'JSC CB "PRIVATBANK", 1D HRUSHEVSKOHO STR., KYIV, 01001, UKRAINE',
    swift: 'PBANUA2X',
    taxId: '3477605484',
    purpose: {
      default: 'Payment for goods',
      withId: 'Payment for goods, order No. {{id}}',
    },
  },
};

// Показується тільки в режимі розробки (npm run dev), щоб бачити вигляд блока.
export const DEV_PLACEHOLDER_DETAILS: BankTransferDetailsData = {
  recipient: 'ТЕСТ: ФОП Прізвище І. Б.',
  iban: 'UA00 0000 0000 0000 0000 0000 00000',
  bank: 'ТЕСТ: Назва банку',
  taxId: '0000000000',
  swift: 'TESTUA00',
};