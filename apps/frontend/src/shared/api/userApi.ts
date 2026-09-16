import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { Address, UserProfile } from '../types/User';


export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery,
  tagTypes: ['User', 'Address'],
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
    getAddress: builder.query<Address, void>({
      query: () => 'auth/me/address/',
      providesTags: ['Address'],
    }),
    updateAddress: builder.mutation<Address, Partial<Address>>({
      query: (body) => ({
        url: 'auth/me/address/',
        method: 'PUT',
        body,
      }),
      invalidatesTags: ['Address', 'User'],
    }),
  }),
});

export const {
  useGetMeQuery,
  useUpdateMeMutation,
  useGetAddressQuery,
  useUpdateAddressMutation,
} = userApi;