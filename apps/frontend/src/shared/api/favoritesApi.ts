import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import { productsApi } from './productsApi';
import type { FavoriteItem, AddFavoriteRequest } from '../types/favorites';
import type { PaginatedResponse } from '../types/common';

export const favoritesApi = createApi({
  reducerPath: 'favoritesApi',
  baseQuery,
  tagTypes: ['Favorites'],
  endpoints: (builder) => ({
    getFavorites: builder.query<
      PaginatedResponse<FavoriteItem>,
      { limit?: number; offset?: number; currency?: string; lang?: string } | undefined
    >({
      query: (params) => ({
        url: 'favorites/',
        params,
      }),
      providesTags: ['Favorites'],
    }),
    addFavorite: builder.mutation<FavoriteItem, AddFavoriteRequest>({
      query: (body) => ({
        url: 'favorites/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Favorites'],
      async onQueryStarted(_arg, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled;
          dispatch(productsApi.util.invalidateTags(['Products']));
        } catch {
          // request failed: nothing to refresh
        }
      },
    }),
    removeFavoriteByProductId: builder.mutation<void, number>({
      query: (productId) => ({
        url: `favorites/by-product/${productId}/`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Favorites'],
      async onQueryStarted(_arg, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled;
          dispatch(productsApi.util.invalidateTags(['Products']));
        } catch {
          // request failed: nothing to refresh
        }
      },
    }),
  }),
});

export const {
  useGetFavoritesQuery,
  useAddFavoriteMutation,
  useRemoveFavoriteByProductIdMutation,
} = favoritesApi;