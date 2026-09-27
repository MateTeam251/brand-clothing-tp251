import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSubmitAvailabilityRequestMutation } from '../../shared/api/productsApi';
import styles from './AvailabilityRequestForm.module.scss';

interface AvailabilityRequestFormProps {
  productId: number;
}

export const AvailabilityRequestForm = ({ productId }: AvailabilityRequestFormProps) => {
  const { t } = useTranslation();
  const [requestName, setRequestName] = useState('');
  const [requestPhone, setRequestPhone] = useState('');
  const [nameError, setNameError] = useState(false);
  const [phoneError, setPhoneError] = useState(false);
  const [requestError, setRequestError] = useState('');
  const [isRequestSent, setIsRequestSent] = useState(false);

  const [submitAvailabilityRequest, { isLoading: isSubmitting }] = useSubmitAvailabilityRequestMutation();

  const handleNameChange = (value: string) => {
    setRequestName(value);
    setNameError(false);
  };

  const handlePhoneChange = (value: string) => {
    setRequestPhone(value);
    setPhoneError(false);
  };

  const handleSubmitRequest = async () => {
    const nameValid = requestName.trim().length > 0;
    const phoneValid = /^\+?\d{9,13}$/.test(requestPhone.replace(/[\s()-]/g, ''));

    setNameError(!nameValid);
    setPhoneError(!phoneValid);

    if (!nameValid || !phoneValid) {
      return;
    }

    setRequestError('');

    try {
      await submitAvailabilityRequest({
        product: productId,
        name: requestName,
        phone_number: requestPhone,
      }).unwrap();
      setIsRequestSent(true);

      setTimeout(() => {
        setIsRequestSent(false);
        setRequestName('');
        setRequestPhone('');
      }, 2000);
    } catch {
      setRequestError(t('generic_error'));
    }
  };

  return (
    <div className={styles.form}>
      <h3 className={styles.form__title}>{t('product.availability_title')}</h3>
      {isRequestSent ? (
        <p>{t('product.request_sent')}</p>
      ) : (
          <>
            <div className={styles.form__fields}>
              <input
                type="text"
                placeholder={t('product.your_name')}
                value={requestName}
                onChange={(e) => handleNameChange(e.target.value)}
                className={nameError ? styles.form__inputError : styles.form__input}
              />
              {nameError && <p className={styles.form__errorText}>{t('product.name_required')}</p>}

              <input
                type="tel"
                placeholder={t('product.phone_number')}
                value={requestPhone}
                onChange={(e) => handlePhoneChange(e.target.value)}
                className={phoneError ? styles.form__inputError : styles.form__input}
              />
              {phoneError && <p className={styles.form__errorText}>{t('product.invalid_phone')}</p>}
            </div>

            <div className={styles.form__submitBlock}>
              <button
                type="button"
                onClick={handleSubmitRequest}
                disabled={isSubmitting}
                className={styles.form__submitBtn}
              >
              {isSubmitting ? t('product.sending') : t('product.send_request')}
              </button>
              {requestError && <p className={styles.form__error}>{requestError}</p>}
              <p className={styles.form__note}>{t('product.availability_note')}</p>
            </div>
        </>
      )}
    </div>
  );
};