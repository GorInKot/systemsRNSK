import { useEffect, useState } from "react";

import { useProfile, useSaveProfile } from "../api/hooks";
import type { ProfileInput } from "../api/types";
import { ErrorState, Loading } from "../components/states";
import { ANKETA, type AnketaField } from "../lib/anketa";

function toForm(profile: ProfileInput): ProfileInput {
  return { ...profile, vkd_rooms: [...profile.vkd_rooms] };
}

export function ProfilePage() {
  const profile = useProfile();
  const save = useSaveProfile();
  const [form, setForm] = useState<ProfileInput | null>(null);

  useEffect(() => {
    if (profile.data && form === null) setForm(toForm(profile.data));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile.data]);

  if (profile.isPending || form === null) return <Loading label="Загружаем анкету…" />;
  if (profile.isError) return <ErrorState error={profile.error} onRetry={() => profile.refetch()} />;

  const dirty = JSON.stringify(form) !== JSON.stringify(toForm(profile.data));

  function setField(name: string, value: unknown) {
    setForm((prev) => (prev ? { ...prev, [name]: value } : prev));
  }

  function toggleCheck(fieldName: string, option: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const current = (prev as unknown as Record<string, unknown>)[fieldName];
      const values = Array.isArray(current) ? (current as string[]) : [];
      const has = values.includes(option);
      const next = has ? values.filter((v) => v !== option) : [...values, option];
      return { ...prev, [fieldName]: next };
    });
  }

  function renderField(field: AnketaField) {
    const value = (form as unknown as Record<string, unknown>)[field.name];

    if (field.type === "checkbox") {
      return (
        <label className="check">
          <input type="checkbox" checked={Boolean(value)} onChange={(e) => setField(field.name, e.target.checked)} />
          {field.label}
        </label>
      );
    }

    if (field.type === "checks") {
      const selected = Array.isArray(value) ? (value as string[]) : [];
      return (
        <div className="field-block">
          <label>{field.label}</label>
          <div className="checks">
            {(field.options ?? []).map((option) => (
              <label key={option}>
                <input type="checkbox" checked={selected.includes(option)} onChange={() => toggleCheck(field.name, option)} />
                {option}
              </label>
            ))}
          </div>
        </div>
      );
    }

    if (field.type === "select") {
      return (
        <div className="field-block">
          <label>{field.label}</label>
          <select value={String(value ?? "")} onChange={(e) => setField(field.name, e.target.value)}>
            {(field.options ?? []).map((option) => (
              <option key={option} value={option}>
                {field.name === "office" ? (option === "head_office" ? "Головной офис" : "Филиал") : option}
              </option>
            ))}
          </select>
        </div>
      );
    }

    const disabled = field.name === "email" && Boolean(form?.no_email);
    return (
      <div className={`field-block${field.wide ? " field-block--wide" : ""}`}>
        <label>{field.label}</label>
        <input
          type={field.type === "date" ? "date" : "text"}
          value={String(value ?? "")}
          placeholder={field.placeholder}
          disabled={disabled}
          onChange={(e) => setField(field.name, e.target.value || null)}
        />
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Анкета</h1>
      <p className="muted">
        Заполните анкету один раз — данные сохранятся на сервере. На вкладке «Заявки» из них в один клик собирается любой документ.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate(form);
        }}
      >
        {ANKETA.map((section) => (
          <fieldset key={section.title} className="sect">
            <legend>{section.title}</legend>
            <div className="cols">
              {section.fields.map((field) => (
                <div key={field.name} className={field.type === "checkbox" ? "field field-check" : `field${field.wide ? " wide" : ""}`}>
                  {renderField(field)}
                </div>
              ))}
            </div>
          </fieldset>
        ))}

        <div className="bar">
          <span className="muted">
            {save.isPending ? "Сохраняем…" : dirty ? "Есть несохранённые изменения" : "Сохранено"}
          </span>
          <button type="submit" className="btn btn--primary" disabled={!dirty || save.isPending}>
            Сохранить
          </button>
        </div>
        {save.isError && <ErrorState error={save.error} />}
      </form>
    </div>
  );
}
