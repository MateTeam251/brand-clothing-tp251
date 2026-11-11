import { PhoneInput } from 'react-international-phone';
import 'react-international-phone/style.css';
import { normalizePhone } from '../../shared/utils/phone';
import styles from './PhoneField.module.scss';

interface PhoneFieldProps {
  name: string;
  label: string;
  value: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  error?: string;
  visibleLabel?: boolean;
}

export const PhoneField = ({
  name,
  label,
  value,
  onChange,
  disabled,
  error,
  visibleLabel,
}: PhoneFieldProps) => {
  const errorId = `${name}-error`;
  const phoneClassName = error ? `${styles.phone} ${styles['phone--error']}` : styles.phone;

  return (
    <div className={styles.field}>
      {visibleLabel && (
        <label htmlFor={name} className={styles.field__label}>
          {label}
        </label>
      )}
      <PhoneInput
        defaultCountry="ua"
        value={normalizePhone(value)}
        onChange={(phone, { country }) => {
          const trunkPrefix = `+${country.dialCode}0`;
          const cleanPhone =
            country.iso2 === 'ua' && phone.startsWith(trunkPrefix)
              ? `+${country.dialCode}${phone.slice(trunkPrefix.length)}`
              : phone;
          const hasNumber = cleanPhone.replace(/\D/g, '').length > country.dialCode.length;
          onChange?.(hasNumber ? cleanPhone : '');
        }}
        disabled={disabled}
        disableDialCodeAndPrefix
        showDisabledDialCodeAndPrefix
        placeholder={visibleLabel ? undefined : label}
        className={phoneClassName}
        inputProps={{
          id: name,
          name,
          type: 'tel',
          autoComplete: 'tel-national',
          'aria-label': label,
          'aria-invalid': Boolean(error),
          'aria-describedby': error ? errorId : undefined,
        }}
      />

      {error && (
        <p id={errorId} className={styles.field__error}>
          {error}
        </p>
      )}
    </div>
  );
};