import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { UserProfile } from '../types/User';

export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  phone_number: string;
  instagram: string;
  agree_to_terms: boolean;
  marketing_opt_in: boolean;
}

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery,
  endpoints: (builder) => ({
    login: builder.mutation<TokenResponse, LoginCredentials>({
      query: (credentials) => ({
        url: 'auth/login/',
        method: 'POST',
        body: credentials,
      }),
    }),
    register: builder.mutation<void, RegisterRequest>({
      query: (body) => ({
        url: 'auth/register/',
        method: 'POST',
        body,
      }),
    }),
     resendActivation: builder.mutation<void, { email: string }>({
      query: (body) => ({
        url: 'auth/resend-activation/',
        method: 'POST',
        body,
      }),
    }),
    refreshToken: builder.mutation<TokenResponse, { refresh: string }>({
      query: (body) => ({
        url: 'auth/refresh/',
        method: 'POST',
        body,
      }),
    }),
    logout: builder.mutation<void, { refresh: string }>({
      query: (body) => ({
        url: 'auth/logout/',
        method: 'POST',
        body,
      }),
    }),
    requestPasswordReset: builder.mutation<void, { email: string }>({
      query: (body) => ({
        url: 'auth/password-reset/',
        method: 'POST',
        body,
      }),
    }),
    confirmPasswordReset: builder.mutation<
      void,
      { uidb64: string; token: string; new_password: string }
    >({
      query: ({ uidb64, token, new_password }) => ({
        url: `auth/reset/${uidb64}/${token}/`,
        method: 'POST',
        body: { new_password },
      }),
    }),
    getUser: builder.query<UserProfile, void>({
      query: () => 'auth/me/',
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useRefreshTokenMutation,
  useLogoutMutation,
  useRequestPasswordResetMutation,
  useConfirmPasswordResetMutation,
  useGetUserQuery,
  useResendActivationMutation,
} = authApi;