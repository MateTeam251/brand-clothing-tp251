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
        url: 'users/token/',
        method: 'POST',
        body: credentials,
      }),
    }),
    getUser: builder.query<UserProfile, void>({
      query: () => 'users/me/',
    }),
  }),
});

export const { useLoginMutation, useGetUserQuery } = authApi;