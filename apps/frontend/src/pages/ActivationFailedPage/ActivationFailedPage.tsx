import { useState } from 'react';
import type { SyntheticEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useResendActivationMutation } from '../../shared/api/authApi';
import { AuthField } from '../../components/AuthField';
import { AuthMessageCard } from '../../components/AuthMessageCard';
import { AuthModalForm } from '../../components/AuthModalForm';
import { useCloseAuth } from '../../shared/hooks/useCloseAuth';

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

type View = 'info' | 'form' | 'sent';

export const ActivationFailedPage = () => {
  const { t } = useTranslation();
  const closeAuth = useCloseAuth();
  const [resendActivation, { isLoading }] = useResendActivationMutation();

  const [view, setView] = useState<View>('info');
  const [email, setEmail] = useState('');
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [formError, setFormError] = useState<string | null>(null);

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
      await resendActivation({ email: trimmedEmail }).unwrap();
      setView('sent');
    } catch (requestError) {
      const status = (requestError as { status?: number }).status;

      setFormError(
        status === 429 ? t('auth.errors.too_many_requests') : t('auth.errors.generic'),
      );
    }
  };

  if (view === 'sent') {
    return (
      <AuthMessageCard
        variant="mail"
        title={t('activation.sent.title')}
        text={t('activation.sent.text')}
        linkTo="/"
        linkLabel={t('activation.failed.home')}
        onClose={closeAuth}
      />
    );
  }

  if (view === 'form') {
    return (
      <AuthMessageCard
        title={t('activation.resend.title')}
        text={t('activation.resend.text')}
        onClose={closeAuth}
      >
        <AuthModalForm
          onSubmit={handleSubmit}
          submitLabel={t('activation.resend.submit')}
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
          />
        </AuthModalForm>
      </AuthMessageCard>
    );
  }

  return (
    <AuthMessageCard
      variant="error"
      title={t('activation.failed.title')}
      text={t('activation.failed.text')}
      primaryLabel={t('activation.failed.resend')}
      onPrimaryClick={() => setView('form')}
      linkTo="/"
      linkLabel={t('activation.failed.home')}
      onClose={closeAuth}
    />
  );
};