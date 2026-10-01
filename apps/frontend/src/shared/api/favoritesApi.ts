import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { FavoriteItem, AddFavoriteRequest } from '../types/favorites';
import type { PaginatedResponse } from '../types/common';

export const favoritesApi = createApi({
  reducerPath: 'favoritesApi',
  baseQuery,
  tagTypes: ['Favorites', 'Products'],
  endpoints: (builder) => ({
    getFavorites: builder.query<PaginatedResponse<FavoriteItem>, { limit?: number; offset?: number } | undefined>({
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
      invalidatesTags: ['Favorites', 'Products'],
    }),
    removeFavoriteByProductId: builder.mutation<void, number>({
      query: (productId) => ({
        url: `favorites/by-product/${productId}/`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Favorites', 'Products'],
    }),
  }),
});

export const {
  useGetFavoritesQuery,
  useAddFavoriteMutation,
  useRemoveFavoriteByProductIdMutation,
} = favoritesApi;