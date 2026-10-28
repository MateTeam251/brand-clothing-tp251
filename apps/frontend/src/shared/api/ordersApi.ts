import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { PaginatedResponse } from '../types/common';
import type { Order, OrderStatusResponse } from '../types/orders';
import type { CheckoutRequest, CheckoutResponse } from '../types/checkout';

export const ordersApi = createApi({
  reducerPath: 'ordersApi',
  baseQuery,
  endpoints: (builder) => ({
    getOrders: builder.query<Order[], void>({
      query: () => ({ url: 'orders/', params: { limit: 100 } }),
      transformResponse: (response: Order[] | PaginatedResponse<Order>) =>
        Array.isArray(response) ? response : response.results,
    }),
    getOrderById: builder.query<Order, string>({
      query: (orderReference) => `orders/${orderReference}/`,
    }),
    getOrderStatus: builder.query<OrderStatusResponse, string>({
      query: (orderReference) => `orders/${orderReference}/status/`,
    }),
    retryPayment: builder.mutation<CheckoutResponse, string>({
      query: (orderReference) => ({
        url: `orders/${orderReference}/retry-payment/`,
        method: 'POST',
      }),
    }),
    checkout: builder.mutation<CheckoutResponse, CheckoutRequest>({
      query: (body) => ({
        url: 'orders/checkout/',
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const {
  useGetOrdersQuery,
  useGetOrderByIdQuery,
  useGetOrderStatusQuery,
  useCheckoutMutation,
  useRetryPaymentMutation,
} = ordersApi;