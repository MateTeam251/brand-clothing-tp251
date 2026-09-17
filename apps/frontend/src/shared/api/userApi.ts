import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { UserProfile } from '../types/User';

export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery,
  tagTypes: ['User'],
  endpoints: (builder) => ({
    getMe: builder.query<UserProfile, void>({
      query: () => 'users/me/',
      providesTags: ['User'],
    }),
    updateMe: builder.mutation<UserProfile, Partial<UserProfile>>({
      query: (body) => ({
        url: 'users/me/',
        method: 'PUT',
        body,
      }),
      invalidatesTags: ['User'],
    }),
  }),
});

export const { useGetMeQuery, useUpdateMeMutation } = userApi;