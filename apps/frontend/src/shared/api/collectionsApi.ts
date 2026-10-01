import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { PaginatedResponse } from '../types/common';
import type { Collection } from '../types/products';

export const collectionsApi = createApi({
  reducerPath: 'collectionsApi',
  baseQuery,
  tagTypes: ['Collections'],
  endpoints: (builder) => ({
    getCollections: builder.query<PaginatedResponse<Collection>, { lang: 'ua' | 'en' }>({
      query: ({ lang }) => ({
        url: 'products/collections/',
        params: { lang },
      }),
      providesTags: ['Collections'],
    }),
  }),
});

export const { useGetCollectionsQuery } = collectionsApi;
