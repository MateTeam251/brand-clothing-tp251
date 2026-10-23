import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { PaginatedResponse } from '../types/common';
import type { DeliveryBranch, DeliveryCity, DeliveryProvider } from '../types/delivery';

export const deliveryApi = createApi({
  reducerPath: 'deliveryApi',
  baseQuery,
  endpoints: (builder) => ({
    getDeliveryCities: builder.query<
      PaginatedResponse<DeliveryCity>,
      { provider: DeliveryProvider; search: string }
    >({
      query: ({ provider, search }) => ({
        url: 'delivery/cities/',
        params: { provider, country: 'UA', search, limit: 20 },
      }),
    }),
    getDeliveryBranches: builder.query<
      PaginatedResponse<DeliveryBranch>,
      { city: number; search: string }
    >({
      query: ({ city, search }) => ({
        url: 'delivery/branches/',
        params: { city, search: search || undefined, limit: 50 },
      }),
    }),
  }),
});

export const { useGetDeliveryCitiesQuery, useGetDeliveryBranchesQuery } = deliveryApi;