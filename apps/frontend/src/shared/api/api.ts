import {
	fetchBaseQuery,
	type BaseQueryFn,
	type FetchArgs,
	type FetchBaseQueryError,
} from '@reduxjs/toolkit/query/react';
import i18n from '../i18n/i18n';

type AuthState = {
  auth: {
    accessToken: string | null;
	};
	settings: {
		language: 'ua' | 'en';
		currency: 'uah' | 'usd';
	};
}

const rawBaseQuery = fetchBaseQuery({
	baseUrl: 'http://127.0.0.1:8000/api/',
	prepareHeaders: (headers, { getState }) => {
		const state = getState() as AuthState;
    const accessToken = state.auth.accessToken;

		if (accessToken) {
			headers.set('Authorization', `Bearer ${accessToken}`);
		}

		return headers;
	},
});

export const baseQuery: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = (
	args,
	api,
	extraOptions,
) => {
	const state = api.getState() as AuthState;
	const request = typeof args === 'string' ? { url: args } : args;

	return rawBaseQuery(
		{
			...request,
			params: {
				...(request.params ?? {}),
				lang: i18n.language,
				currency: state.settings.currency,
			},
		},
		api,
		extraOptions,
	);
};