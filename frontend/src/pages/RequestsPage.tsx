import { useState } from "react";

import { ApiError, download } from "../api/client";
import { useProfile, useSystems } from "../api/hooks";
import type { Profile, System } from "../api/types";
import { ErrorState, Loading } from "../components/states";
import { FIELD_LABELS } from "../lib/anketa";

function isSet(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0;
  return Boolean(value);
}

function missingFields(system: System, profile: Profile): string[] {
  if (!system.ready) return [];
  const data = profile as unknown as Record<string, unknown>;
  return system.need.filter((key) => !isSet(data[key]));
}

export function RequestsPage() {
  const systems = useSystems();
  const profile = useProfile();
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (systems.isPending || profile.isPending) return <Loading label="Загружаем заявки…" />;
  if (systems.isError) return <ErrorState error={systems.error} onRetry={() => systems.refetch()} />;
  if (profile.isError) return <ErrorState error={profile.error} onRetry={() => profile.refetch()} />;

  async function generate(system: System) {
    setErrors((prev) => ({ ...prev, [system.id]: "" }));
    setBusy(system.id);
    try {
      const choice = system.choice ? (choices[system.id] ?? system.choice.options[0]) : undefined;
      await download(`/systems/${system.id}/generate`, { method: "POST", body: { choice } }, `${system.title}.xlsx`);
    } catch (error) {
      setErrors((prev) => ({ ...prev, [system.id]: error instanceof ApiError ? error.message : "Не удалось сформировать заявку." }));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="page">
      <h1>Заявки</h1>
      <p className="muted">Нажмите «Создать и скачать» — заявка сформируется из данных анкеты. Если каких-то полей не хватает, карточка подскажет, что дозаполнить.</p>

      <div className="grid">
        {systems.data.map((system) => {
          const missing = missingFields(system, profile.data);
          const inPrep = !system.ready;
          return (
            <div key={system.id} className={`card${system.hl ? " card--hl" : ""}${inPrep ? " card--locked" : ""}`}>
              <div className="card__top">
                <div className="card__icon">{system.icon}</div>
                <h3>{system.title}</h3>
              </div>
              <p className="card__desc">{system.desc}</p>

              {!inPrep && system.choice && (
                <label className="card__choice">
                  Действие
                  <select
                    value={choices[system.id] ?? system.choice.options[0]}
                    onChange={(e) => setChoices((prev) => ({ ...prev, [system.id]: e.target.value }))}
                  >
                    {system.choice.options.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
              )}

              {inPrep ? (
                <span className="status status--locked">🛠 Шаблон в подготовке</span>
              ) : missing.length ? (
                <p className="card__missing">Дозаполните в анкете: {missing.map((key) => FIELD_LABELS[key] ?? key).join(", ")}</p>
              ) : (
                <span className="status status--done">✓ Готово к формированию</span>
              )}

              {errors[system.id] && <p className="card__missing">{errors[system.id]}</p>}

              <div className="card__acts">
                <button
                  type="button"
                  className="btn btn--primary btn--small"
                  disabled={inPrep || missing.length > 0 || busy === system.id}
                  onClick={() => generate(system)}
                >
                  {busy === system.id ? "Формируем…" : "Создать и скачать"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
