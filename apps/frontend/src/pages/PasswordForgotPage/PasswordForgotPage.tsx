import { useState } from 'react';
import type { SyntheticEvent } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useRequestPasswordResetMutation } from '../../shared/api/authApi';
import { AuthField } from '../../components/AuthField';
import { AuthMessageCard } from '../../components/AuthMessageCard';
import { AuthModalForm } from '../../components/AuthModalForm';
import styles from './PasswordForgotPage.module.scss';
import { useCloseAuth } from '../../shared/hooks/useCloseAuth';

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

export const PasswordForgotPage = () => {
  const { t } = useTranslation();
  const [requestReset, { isLoading }] = useRequestPasswordResetMutation();
  const location = useLocation();
  const initialEmail = (location.state as { email?: string } | null)?.email ?? '';

  const [email, setEmail] = useState(initialEmail);
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [formError, setFormError] = useState<string | null>(null);
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [isResent, setIsResent] = useState(false);
  const closeAuth = useCloseAuth();

  const getErrorText = (error: unknown) => {
    const status = (error as { status?: number }).status;

    return status === 429 ? t('auth.errors.too_many_requests') : t('auth.errors.generic');
  };

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedEmail = email.trim();
    let error: string | undefined;

    if (!trimmedEmail) {
      error = t('auth.errors.required');
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      error = t('auth.errors.invalid_email');
    }

    setFieldError(error);
    setFormError(null);

    if (error) {
      return;
    }

    try {
      await requestReset({ email: trimmedEmail }).unwrap();
      setSentTo(trimmedEmail);
    } catch (requestError) {
      setFormError(getErrorText(requestError));
    }
  };

  const handleResend = async () => {
    if (!sentTo) {
      return;
    }

    setFormError(null);

    try {
      await requestReset({ email: sentTo }).unwrap();
      setIsResent(true);
    } catch (requestError) {
      setFormError(getErrorText(requestError));
    }
  };

  if (sentTo) {
    return (
      <AuthMessageCard
        variant="mail"
        title={t('password_recovery.check_email.title')}
        text={t('password_recovery.check_email.text')}
        onClose={closeAuth}
      >
        {isResent ? (
          <p className={styles.notice}>{t('password_recovery.check_email.resent')}</p>
        ) : (
          <button
            type="button"
            className={styles.resend}
            onClick={handleResend}
            disabled={isLoading}
          >
            {t('password_recovery.check_email.resend')}
          </button>
        )}
        {formError && <p className={styles.error}>{formError}</p>}
      </AuthMessageCard>
    );
  }

  return (
    <AuthMessageCard
      title={t('password_recovery.title')}
      text={t('password_recovery.subtitle')}
      onClose={closeAuth}
    >
      <AuthModalForm
        onSubmit={handleSubmit}
        submitLabel={t('password_recovery.submit')}
        isSubmitting={isLoading}
        error={formError}
      >
        <AuthField
          name="email"
          type="email"
          label={t('auth.email')}
          value={email}
          onChange={setEmail}
          error={fieldError}
          autoComplete="email"
          disabled={Boolean(initialEmail)}
        />
      </AuthModalForm>
    </AuthMessageCard>
  );
};