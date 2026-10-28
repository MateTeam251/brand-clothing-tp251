import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  BANK_TRANSFER_DETAILS,
  DEV_PLACEHOLDER_DETAILS,
} from '../../shared/config/bankTransferDetails';
import type { Currency } from '../../shared/types/orders';
import styles from './BankTransferDetails.module.scss';

interface BankTransferDetailsProps {
  currency: Currency;
  orderId?: string;
}

export function BankTransferDetails({ currency, orderId }: BankTransferDetailsProps) {
  const { t } = useTranslation();
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const details =
    BANK_TRANSFER_DETAILS[currency] ??
    (import.meta.env.DEV ? DEV_PLACEHOLDER_DETAILS : null);

  if (!details) {
    return null;
  }

  const purpose = orderId
    ? t('bank_transfer.purpose_with_id', { id: orderId })
    : t('bank_transfer.purpose');

  const rows = [
    { key: 'recipient', label: t('bank_transfer.recipient'), value: details.recipient },
    { key: 'iban', label: t('bank_transfer.iban'), value: details.iban },
    { key: 'taxId', label: t('bank_transfer.tax_id'), value: details.taxId },
    { key: 'bank', label: t('bank_transfer.bank'), value: details.bank },
    ...(details.swift
      ? [{ key: 'swift', label: t('bank_transfer.swift'), value: details.swift }]
      : []),
    { key: 'purpose', label: t('bank_transfer.purpose_label'), value: purpose },
  ];

  const handleCopy = async (key: string, value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey(null), 2000);
    } catch {
      // буфер обміну недоступний: користувач може скопіювати текст вручну
    }
  };

  return (
    <details className={styles.details}>
      <summary className={styles.details__summary}>{t('bank_transfer.title')}</summary>

      <p className={styles.details__hint}>{t('bank_transfer.hint')}</p>

      <dl className={styles.details__list}>
        {rows.map((row) => (
          <div key={row.key} className={styles.details__row}>
            <dt className={styles.details__label}>{row.label}</dt>
            <dd className={styles.details__value}>
              <span>{row.value}</span>
              <button
                type="button"
                className={styles.details__copy}
                onClick={() => void handleCopy(row.key, row.value)}
              >
                {copiedKey === row.key
                  ? t('bank_transfer.copied')
                  : t('bank_transfer.copy')}
              </button>
            </dd>
          </div>
        ))}
      </dl>
    </details>
  );
}