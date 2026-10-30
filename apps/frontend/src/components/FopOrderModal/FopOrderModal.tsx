import { useTranslation } from 'react-i18next';
import type { Currency } from '../../shared/types/orders';
import { AuthMessageCard } from '../AuthMessageCard';
import { BankTransferDetails } from '../BankTransferDetails';

interface FopOrderModalProps {
  orderReference: string;
  currency: Currency;
  onClose: () => void;
}

export const FopOrderModal = ({ orderReference, currency, onClose }: FopOrderModalProps) => {
  const { t } = useTranslation();

  return (
    <AuthMessageCard
      title={t('bank_transfer.order_created_title')}
      text={t('bank_transfer.order_created_text')}
      primaryLabel={t('bank_transfer.order_created_done')}
      onPrimaryClick={onClose}
      onClose={onClose}
    >
      <BankTransferDetails currency={currency} orderId={orderReference} defaultOpen />
    </AuthMessageCard>
  );
};