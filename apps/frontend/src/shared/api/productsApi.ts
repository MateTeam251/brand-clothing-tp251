import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { PaginatedResponse } from '../types/common';
import type { ProductDetails, ProductListItem, ProductQueryParams } from '../types/products';

export const productsApi = createApi({
  reducerPath: 'productsApi',
  baseQuery,
  tagTypes: ['Products'],
  endpoints: (builder) => ({
    getProducts: builder.query<PaginatedResponse<ProductListItem>, ProductQueryParams | undefined>({
      query: (params) => ({
        url: 'products/',
        params,
      }),
      providesTags: ['Products'],
    }),
    getProductById: builder.query<ProductDetails, { id: number } & ProductQueryParams>({
      query: ({ id, ...params }) => ({
        url: `products/${id}/`,
        params,
      }),
      providesTags: ['Products'],
    }),
  }),
});

export const { useGetProductsQuery, useGetProductByIdQuery } = productsApi;