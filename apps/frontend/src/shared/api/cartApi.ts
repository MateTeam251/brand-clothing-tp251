import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { AddCartItemBody, Cart, CartQueryArg } from '../types/Cart';

export const cartApi = createApi({
  reducerPath: 'cartApi',
  baseQuery,
  tagTypes: ['Cart'],
  endpoints: (builder) => ({
    getCart: builder.query<Cart, CartQueryArg>({
      query: ({ currency }) => ({
        url: 'cart/',
        params: { currency },
      }),
      providesTags: ['Cart'],
    }),
    addCartItem: builder.mutation<unknown, AddCartItemBody>({
      query: (body) => ({
        url: 'cart/items/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Cart'],
    }),
    updateCartItemQuantity: builder.mutation<unknown, { id: number; quantity: number }>({
      query: ({ id, quantity }) => ({
        url: `cart/items/${id}/`,
        method: 'PATCH',
        body: { quantity },
      }),
      invalidatesTags: ['Cart'],
    }),
    removeCartItem: builder.mutation<void, number>({
      query: (id) => ({
        url: `cart/items/${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Cart'],
    }),
    changeCartItemSize: builder.mutation<
      void,
      { id: number; product: number; quantity: number; size: string }
    >({
      async queryFn({ id, product, quantity, size }, _api, _extraOptions, fetchWithBQ) {
        const added = await fetchWithBQ({
          url: 'cart/items/',
          method: 'POST',
          body: { product, size, quantity },
        });

        if (added.error) {
          return { error: added.error };
        }

        const removed = await fetchWithBQ({
          url: `cart/items/${id}/`,
          method: 'DELETE',
        });

        if (removed.error) {
          return { error: removed.error };
        }

        return { data: undefined };
      },
      invalidatesTags: ['Cart'],
    }),
  }),
});

export const {
  useGetCartQuery,
  useAddCartItemMutation,
  useUpdateCartItemQuantityMutation,
  useRemoveCartItemMutation,
  useChangeCartItemSizeMutation,
} = cartApi;