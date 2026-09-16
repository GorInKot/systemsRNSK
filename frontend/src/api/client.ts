import type { FieldError } from "./types";

const BASE = `${import.meta.env.BASE_URL}api`;
const DEV_USER_KEY = "dostup.devUser";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code: string | null = null,
    public errors: FieldError[] = [],
  ) {
    super(message);
  }
}

export function getDevUser(): string | null {
  try {
    return localStorage.getItem(DEV_USER_KEY);
  } catch {
    return null;
  }
}

export function setDevUser(login: string): void {
  try {
    localStorage.setItem(DEV_USER_KEY, login);
  } catch {
    /* хранилище недоступно — останется пользователь по умолчанию */
  }
}

type QueryValue = string | number | boolean | null | undefined;

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, QueryValue>;
  signal?: AbortSignal;
}

export function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null || value === "") continue;
    params.set(key, String(value));
  }
  const search = params.toString();
  return `${BASE}${path}${search ? `?${search}` : ""}`;
}

const STATUS_MESSAGES: Record<number, string> = {
  401: "Не удалось определить пользователя. Обновите страницу портала.",
  403: "Недостаточно прав для этого действия.",
  404: "Запрошенные данные не найдены.",
  409: "Действие сейчас недоступно.",
  500: "Внутренняя ошибка сервера. Повторите действие; если ошибка повторится, сообщите в поддержку.",
  502: "Сервер временно недоступен. Повторите через минуту.",
  503: "Сервер временно недоступен. Повторите через минуту.",
};

async function send(path: string, options: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = { "X-Requested-With": "dostup", Accept: "application/json" };
  const devUser = getDevUser();
  if (devUser) headers["X-Dev-User"] = devUser;
  let body: BodyInit | undefined;
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, options.query), {
      method: options.method ?? "GET",
      headers,
      body,
      credentials: "same-origin",
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "Нет связи с сервером. Проверьте подключение и повторите действие.", "network");
  }

  if (!response.ok) {
    let payload: { message?: string; code?: string; errors?: FieldError[] } = {};
    try {
      payload = await response.json();
    } catch {
      /* ответ не JSON — используем сообщение по коду */
    }
    throw new ApiError(
      response.status,
      payload.message ?? STATUS_MESSAGES[response.status] ?? `Ошибка ${response.status}`,
      payload.code ?? null,
      payload.errors ?? [],
    );
  }
  return response;
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(path, options);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** Скачивание сгенерированного файла заявки через fetch: уходит с теми же заголовками, что и остальные запросы. */
export async function download(path: string, options: RequestOptions, fallbackName: string): Promise<void> {
  const response = await send(path, options);
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  const name = match ? decodeURIComponent(match[1]) : fallbackName;
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
