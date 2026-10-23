import { useTranslation } from 'react-i18next';
import { AuthField } from '../AuthField';
import type {
  CheckoutContactErrors,
  CheckoutContactValues,
} from '../../shared/types/checkout';
import styles from './CheckoutContactForm.module.scss';

interface CheckoutContactFormProps {
  values: CheckoutContactValues;
  errors?: CheckoutContactErrors;
  onChange: (field: keyof CheckoutContactValues, value: string) => void;
}

export const CheckoutContactForm = ({
  values,
  errors = {},
  onChange,
}: CheckoutContactFormProps) => {
  const { t } = useTranslation();

  return (
    <section className={styles.contact}>
      <h2 className={styles.contact__title}>{t('checkout.contact_title')}</h2>

      <div className={styles.contact__fields}>
        <AuthField
          name="checkout-first-name"
          label={t('checkout.first_name')}
          value={values.first_name}
          onChange={(value) => onChange('first_name', value)}
          error={errors.first_name}
          autoComplete="given-name"
        />
        <AuthField
          name="checkout-last-name"
          label={t('checkout.last_name')}
          value={values.last_name}
          onChange={(value) => onChange('last_name', value)}
          error={errors.last_name}
          autoComplete="family-name"
        />
        <AuthField
          name="checkout-phone"
          type="tel"
          label={t('checkout.phone')}
          value={values.phone}
          onChange={(value) => onChange('phone', value)}
          error={errors.phone}
          autoComplete="tel"
        />
        <AuthField
          name="checkout-email"
          type="email"
          label={t('checkout.email')}
          value={values.email}
          onChange={(value) => onChange('email', value)}
          error={errors.email}
          autoComplete="email"
        />
      </div>
    </section>
  );
};