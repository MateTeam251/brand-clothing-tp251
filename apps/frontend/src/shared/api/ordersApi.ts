import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { PaginatedResponse } from '../types/common';
import type { Order } from '../types/orders';

export const ordersApi = createApi({
  reducerPath: 'ordersApi',
  baseQuery,
  endpoints: (builder) => ({
    getOrders: builder.query<Order[], void>({
      query: () => ({ url: 'orders/', params: { limit: 100 } }),
      transformResponse: (response: Order[] | PaginatedResponse<Order>) =>
        Array.isArray(response) ? response : response.results,
    }),
    getOrderById: builder.query<Order, number>({
      query: (id) => `orders/${id}/`,
    }),
  }),
});

export const { useGetOrdersQuery, useGetOrderByIdQuery } = ordersApi;