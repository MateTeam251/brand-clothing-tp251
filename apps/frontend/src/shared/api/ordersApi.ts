import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { Order } from '../types/orders';

export const ordersApi = createApi({
  reducerPath: 'ordersApi',
  baseQuery,
  endpoints: (builder) => ({
    getOrders: builder.query<Order[], void>({
      query: () => 'orders/',
    }),
    getOrderById: builder.query<Order, number>({
      query: (id) => `orders/${id}/`,
    }),
  }),
});

export const { useGetOrdersQuery, useGetOrderByIdQuery } = ordersApi;