import type { User } from "../types/User";

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export type TokenResponse = {
  access: string;
  refresh: string;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, options);

  if(!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const getUser = async (accessToken: string) => {
  return request<User>(`/users/me/`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    }
  });
}

export const loginUser = async (email: string, password: string) => {
  return request<TokenResponse>(`/users/token/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
};