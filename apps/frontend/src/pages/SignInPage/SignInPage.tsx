import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useLoginMutation } from '../../shared/api/authApi';
import { setCredentials } from '../../app/store/reducers/authSlice';
import { useAppDispatch, useAppSelector } from '../../shared/hooks/reduxHooks';
import { AuthCard } from '../../components/AuthCard';
import { AuthField } from '../../components/AuthField';
import styles from './SignInPage.module.scss';

type FieldErrors = {
  email?: string;
  password?: string;
};

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

const getRedirectPath = (state: unknown): string => {
  const from = (state as { from?: { pathname?: string; search?: string; hash?: string } } | null)
    ?.from;

  if (!from?.pathname || from.pathname === '/signin') {
    return '/account';
  }

  return `${from.pathname}${from.search ?? ''}${from.hash ?? ''}`;
};

export const SignInPage = () => {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const location = useLocation();
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const [login, { isLoading }] = useLoginMutation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);

  if (isAuthenticated) {
    return <Navigate to={getRedirectPath(location.state)} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedEmail = email.trim();
    const errors: FieldErrors = {};

    if (!trimmedEmail) {
      errors.email = t('auth.errors.required');
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      errors.email = t('auth.errors.invalid_email');
    }

    if (!password) {
      errors.password = t('auth.errors.required');
    }

    setFieldErrors(errors);
    setFormError(null);

    if (Object.keys(errors).length > 0) {
      return;
    }

    try {
      const tokens = await login({ email: trimmedEmail, password }).unwrap();
      dispatch(setCredentials(tokens));
    } catch (error) {
      const status = (error as { status?: number }).status;

      if (status === 401) {
        setFormError(t('auth.errors.invalid_credentials'));
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
      submitLabel={t('auth.sign_in')}
      isSubmitting={isLoading}
      error={formError}
      footer={
        <Link to="/forgotpassword" className={styles.signIn__forgot}>
          {t('auth.forgot_password')}
        </Link>
      }
    >
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
        name="password"
        type="password"
        label={t('auth.password')}
        value={password}
        onChange={setPassword}
        error={fieldErrors.password}
        autoComplete="current-password"
      />
    </AuthCard>
  );
};
