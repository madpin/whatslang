/**
 * Tiny typed fetch wrapper. Cookies are sent automatically (same-origin).
 * On 401, dispatches a `whatslang:unauthorized` event so the app shell
 * can route the user to the login page.
 */
export class ApiError extends Error {
  status: number;
  detail?: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  query?: Record<string, string | number | boolean | undefined | null>;
  body?: unknown;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(path, window.location.origin);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null || v === '') continue;
      url.searchParams.set(k, String(v));
    }
  }
  return url.pathname + url.search;
}

async function parseJson(res: Response) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function request<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { query, body, headers, ...rest } = options;
  const init: RequestInit = {
    ...rest,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(headers ?? {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  };
  const res = await fetch(buildUrl(path, query), init);

  if (res.status === 401) {
    window.dispatchEvent(new CustomEvent('whatslang:unauthorized'));
  }

  const data = await parseJson(res);
  if (!res.ok) {
    const detail =
      (data && typeof data === 'object' && 'detail' in (data as object)
        ? (data as { detail: unknown }).detail
        : undefined) ?? data;
    const msg =
      typeof detail === 'string' ? detail : `${res.status} ${res.statusText}`;
    throw new ApiError(res.status, msg, detail);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...(opts ?? {}), method: 'GET' }),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...(opts ?? {}), method: 'POST', body }),
  put: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...(opts ?? {}), method: 'PUT', body }),
  delete: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...(opts ?? {}), method: 'DELETE' }),
};
