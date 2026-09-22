// Секции и поля анкеты — переносит ANKETA из прежнего прототипа (см. LOGIC.md в корне репозитория).
// Действия ПКЗИ/VipNet сюда не входят — их варианты приходят с бэкенда в System.choice
// и выбираются прямо на карточке заявки, а не в анкете.

export const VKD_ACTIONS = [
  "Предоставление доступа Пользователям ВКД",
  "Изменение атрибутов УЗ Пользователей ВКД",
  "Прекращение (изъятие) доступа Пользователей ВКД",
  "Блокировка УЗ в ИС ВКД Пользователей ВКД",
  "Согласование полномочий, присвоенных ранее в экстренном порядке",
];

export const VKD_ROOMS = ["РНСК", "РНСК КомНПЗ", "РНСК Красноярск", "РНСК Тюмень", "РНСК Уфа"];

export type FieldType = "text" | "select" | "date" | "checkbox" | "checks";

export interface AnketaField {
  name: string;
  label: string;
  type?: FieldType;
  wide?: boolean;
  placeholder?: string;
  options?: string[];
  disables?: string;
}

export interface AnketaSection {
  title: string;
  fields: AnketaField[];
}

export const ANKETA: AnketaSection[] = [
  {
    title: "Офис",
    fields: [{ name: "office", label: "Офис", type: "select", options: ["head_office", "branch"] }],
  },
  {
    title: "Личные данные",
    fields: [
      { name: "full_name", label: "Ф.И.О. (полностью)", wide: true, placeholder: "Иванов Иван Иванович" },
      { name: "position", label: "Должность" },
      { name: "phone", label: "Телефон" },
      { name: "order_number", label: "№ приказа о приёме", placeholder: "86-к" },
      { name: "order_date", label: "Дата приказа", type: "date" },
      { name: "department", label: "Наименование структурного подразделения", wide: true },
      { name: "email", label: "E-mail", placeholder: "II_Ivanov@rnsk.rosneft.ru" },
      { name: "no_email", label: "Нет E-mail", type: "checkbox", disables: "email" },
      { name: "account_name", label: "Имя учётной записи", wide: true, placeholder: "ROSNEFT\\i.ivanov" },
      { name: "pkzi_name", label: "Имя ключа ПКЗИ", wide: true, placeholder: "StroyKontrol_IvanovII" },
    ],
  },
  {
    title: "Руководитель",
    fields: [
      { name: "manager_full_name", label: "Ф.И.О. руководителя", wide: true },
      { name: "manager_position", label: "Должность руководителя" },
      { name: "manager_phone", label: "Телефон руководителя" },
    ],
  },
  {
    title: "Параметры ВКД",
    fields: [
      { name: "vkd_action", label: "Действие ВКД", type: "select", options: VKD_ACTIONS },
      { name: "vkd_rooms", label: "Наименование ВКД (можно несколько)", type: "checks", options: VKD_ROOMS, wide: true },
    ],
  },
  {
    title: "Параметры ЦУС",
    fields: [
      { name: "seid_role", label: "Роль в ИР СЭИД", wide: true, placeholder: "(Строительный контроль) - Инженер СК" },
    ],
  },
];

export const OFFICE_LABELS: Record<string, string> = { head_office: "Головной офис", branch: "Филиал" };

export const FIELD_LABELS: Record<string, string> = Object.fromEntries(
  ANKETA.flatMap((section) => section.fields.map((field) => [field.name, field.label])),
);
