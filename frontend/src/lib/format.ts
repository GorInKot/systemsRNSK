/** Русское склонение по числу: plural(5, ["сотрудник", "сотрудника", "сотрудников"]) → "сотрудников". */
export function plural(count: number, forms: [string, string, string]): string {
  const n = Math.abs(count) % 100;
  const n1 = n % 10;
  if (n > 10 && n < 20) return forms[2];
  if (n1 > 1 && n1 < 5) return forms[1];
  if (n1 === 1) return forms[0];
  return forms[2];
}

/** "2020-12-11" → "11.12.2020". Пусто/некорректно — null. */
export function formatRuDate(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const [year, month, day] = iso.split("-");
  if (!year || !month || !day) return null;
  return `${day}.${month}.${year}`;
}

/** Значение для отображения в таблице: пустая строка/null/undefined → «—» (не путать со скрытой ошибкой). */
export function orDash(value: string | null | undefined): string {
  return value && value.trim() ? value : "—";
}
