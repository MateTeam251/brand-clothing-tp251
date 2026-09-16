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

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery,
  endpoints: (builder) => ({
    login: builder.mutation<TokenResponse, LoginCredentials>({
      query: (credentials) => ({
        url: 'auth/token/',
        method: 'POST',
        body: credentials,
      }),
    }),
    refreshToken: builder.mutation<TokenResponse, { refresh: string }>({
      query: (body) => ({
        url: 'auth/refresh/',
        method: 'POST',
        body,
      }),
    }),
    getUser: builder.query<UserProfile, void>({
      query: () => 'auth/me/',
    }),
  }),
});

export const { useLoginMutation, useRefreshTokenMutation, useGetUserQuery } = authApi;