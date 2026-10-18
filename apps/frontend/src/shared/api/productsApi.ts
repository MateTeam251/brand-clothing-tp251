import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery } from './api';
import type { PaginatedResponse } from '../types/common';
import type { ProductDetails, ProductListItem, ProductQueryParams } from '../types/products';

export interface AvailabilityRequestBody {
  product: number;
  name: string;
  phone_number: string;
}

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
        getProductsByIds: builder.query<ProductDetails[], { ids: number[] } & ProductQueryParams>({
      async queryFn({ ids, ...params }, _api, _extraOptions, fetchWithBQ) {
        const results = await Promise.all(
          ids.map((id) => fetchWithBQ({ url: `products/${id}/`, params })),
        );

        const products: ProductDetails[] = [];

        for (const result of results) {
          if (result.error) {
          
            if (result.error.status === 404) {
              continue;
            }

            return { error: result.error };
          }

          products.push(result.data as ProductDetails);
        }

        return { data: products };
      },
      providesTags: ['Products'],
    }),
    submitAvailabilityRequest: builder.mutation<AvailabilityRequestBody, AvailabilityRequestBody>({
      query: (body) => ({
        url: 'products/availability-requests/',
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const {
  useGetProductsQuery,
  useGetProductByIdQuery,
  useGetProductsByIdsQuery,
  useSubmitAvailabilityRequestMutation
} = productsApi;