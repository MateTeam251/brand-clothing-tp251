import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { UserProfile } from '../types/User';

export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery,
  tagTypes: ['User'],
  endpoints: (builder) => ({
    getMe: builder.query<UserProfile, void>({
      query: () => 'auth/me/',
      providesTags: ['User'],
    }),
    updateMe: builder.mutation<UserProfile, Partial<UserProfile>>({
      query: (body) => ({
        url: 'auth/me/',
        method: 'PUT',
        body,
      }),
      invalidatesTags: ['User'],
    }),
    changePassword: builder.mutation<
      { detail: string },
      { old_password: string; new_password: string; new_password_confirm: string }
    >({
      query: (body) => ({
        url: 'auth/me/password/',
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const { useGetMeQuery, useUpdateMeMutation, useChangePasswordMutation } = userApi;