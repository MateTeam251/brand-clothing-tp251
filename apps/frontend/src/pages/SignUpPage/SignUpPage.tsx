import { useState } from 'react';
import type { SyntheticEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useRegisterMutation } from '../../shared/api/authApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import { AuthCard } from '../../components/AuthCard';
import { AuthField } from '../../components/AuthField';
import { AuthCheckbox } from '../../components/AuthCheckbox';
import { AuthMessageCard } from '../../components/AuthMessageCard';

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

const FIELD_KEYS = [
  'email',
  'password',
  'password_confirm',
  'instagram',
  'agree_to_terms',
] as const;

type FieldKey = (typeof FIELD_KEYS)[number];
type FieldErrors = Partial<Record<FieldKey, string>>;

// Бекенд при 400 повертає { поле: ["текст помилки"] } — беремо перший текст
const mapServerErrors = (data: unknown): FieldErrors => {
  const result: FieldErrors = {};

  if (!data || typeof data !== 'object') {
    return result;
  }

  FIELD_KEYS.forEach((key) => {
    const value = (data as Record<string, unknown>)[key];
    const message = Array.isArray(value) ? value[0] : value;

    if (typeof message === 'string') {
      result[key] = message;
    }
  });

  return result;
};

export const SignUpPage = () => {
  const { t } = useTranslation();
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const [register, { isLoading }] = useRegisterMutation();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [instagram, setInstagram] = useState('');
  const [agree, setAgree] = useState(false);
  const [marketing, setMarketing] = useState(false);

  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  if (isAuthenticated) {
    return <Navigate to="/account" replace />;
  }

  if (registeredEmail) {
    return (
      <AuthMessageCard
        variant="mail"
        title={t('sign_up.check_email.title')}
        text={t('sign_up.check_email.text', { email: registeredEmail })}
        linkTo="/"
        linkLabel={t('sign_up.check_email.home')}
      />
    );
  }

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedEmail = email.trim();
    const trimmedInstagram = instagram.trim();
    const errors: FieldErrors = {};

    if (!trimmedEmail) {
      errors.email = t('auth.errors.required');
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      errors.email = t('auth.errors.invalid_email');
    }

    if (!password) {
      errors.password = t('auth.errors.required');
    }

    if (!passwordConfirm) {
      errors.password_confirm = t('auth.errors.required');
    } else if (password !== passwordConfirm) {
      errors.password_confirm = t('sign_up.errors.password_mismatch');
    }

    if (!trimmedInstagram) {
      errors.instagram = t('auth.errors.required');
    }

    if (!agree) {
      errors.agree_to_terms = t('sign_up.errors.agree_required');
    }

    setFieldErrors(errors);
    setFormError(null);

    if (Object.keys(errors).length > 0) {
      return;
    }

    try {
      await register({
        email: trimmedEmail,
        password,
        password_confirm: passwordConfirm,
        name: name.trim() || undefined,
        instagram: trimmedInstagram,
        agree_to_terms: agree,
        marketing_opt_in: marketing,
      }).unwrap();

      setRegisteredEmail(trimmedEmail);
    } catch (error) {
      const { status, data } = error as { status?: number; data?: unknown };

      if (status === 400) {
        const serverErrors = mapServerErrors(data);

        if (Object.keys(serverErrors).length > 0) {
          setFieldErrors(serverErrors);
        } else {
          setFormError(t('auth.errors.generic'));
        }
      } else if (status === 429) {
        setFormError(t('auth.errors.too_many_requests'));
      } else {
        setFormError(t('auth.errors.generic'));
      }
    }
  };

  return (
    <AuthCard
      onSubmit={handleSubmit}
      submitLabel={t('sign_up.submit')}
      isSubmitting={isLoading}
      error={formError}
    >
      <AuthField
        name="name"
        type="text"
        label={t('profile.name')}
        value={name}
        onChange={setName}
        autoComplete="name"
      />
      <AuthField
        name="email"
        type="email"
        label={t('auth.email')}
        value={email}
        onChange={setEmail}
        error={fieldErrors.email}
        autoComplete="email"
      />
      <AuthField
        name="instagram"
        type="text"
        label={t('profile.instagram')}
        value={instagram}
        onChange={setInstagram}
        error={fieldErrors.instagram}
      />
      <AuthField
        name="password"
        type="password"
        label={t('auth.password')}
        value={password}
        onChange={setPassword}
        error={fieldErrors.password}
        autoComplete="new-password"
      />
      <AuthField
        name="password_confirm"
        type="password"
        label={t('sign_up.password_confirm')}
        value={passwordConfirm}
        onChange={setPasswordConfirm}
        error={fieldErrors.password_confirm}
        autoComplete="new-password"
      />
      <AuthCheckbox
        name="agree_to_terms"
        checked={agree}
        onChange={setAgree}
        label={t('sign_up.agree')}
        error={fieldErrors.agree_to_terms}
      />
      <AuthCheckbox
        name="marketing_opt_in"
        checked={marketing}
        onChange={setMarketing}
        label={t('profile.marketing')}
      />
    </AuthCard>
  );
};