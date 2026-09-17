import { useState } from "react";

import { useCreateEmployee, useDeleteEmployee, useEmployees, useUpdateEmployee } from "../../api/hooks";
import type { EmployeeAdmin } from "../../api/types";
import { Dialog } from "../../components/Dialog";
import { ErrorState, Loading, Pagination } from "../../components/states";
import { formatRuDate } from "../../lib/format";

const PAGE_SIZE = 20;

type EmployeeFormState = {
  id: number | null;
  full_name: string;
  position: string;
  phone: string;
  email: string;
  department: string;
  manager_full_name: string;
  manager_position: string;
  manager_phone: string;
  order_number: string;
  order_date: string;
};

const EMPTY_FORM: EmployeeFormState = {
  id: null,
  full_name: "",
  position: "",
  phone: "",
  email: "",
  department: "",
  manager_full_name: "",
  manager_position: "",
  manager_phone: "",
  order_number: "",
  order_date: "",
};

function toForm(employee: EmployeeAdmin): EmployeeFormState {
  return {
    id: employee.id,
    full_name: employee.full_name,
    position: employee.position,
    phone: employee.phone,
    email: employee.email ?? "",
    department: employee.department,
    manager_full_name: employee.manager_full_name,
    manager_position: employee.manager_position,
    manager_phone: employee.manager_phone,
    order_number: employee.order_number ?? "",
    order_date: employee.order_date ?? "",
  };
}

/** ФИО сотрудника построчно: фамилия, имя, отчество — экономит горизонтальное место. */
function NameCell({ fullName }: { fullName: string }) {
  if (!fullName) return <span className="cell__empty">—</span>;
  const parts = fullName.trim().split(/\s+/);
  return (
    <div className="cell">
      {parts.map((part, index) => (
        <div className="cell__title" key={index}>
          {part}
        </div>
      ))}
    </div>
  );
}

/** Ячейка «заголовок + подпись»: например ФИО руководителя сверху, должность и телефон снизу помельче. */
function StackCell({ title, meta }: { title: string; meta?: string | null }) {
  if (!title) return <span className="cell__empty">—</span>;
  return (
    <div className="cell">
      <div className="cell__title">{title}</div>
      {meta && <div className="cell__meta">{meta}</div>}
    </div>
  );
}

function ContactsCell({ phone, email }: { phone: string; email: string | null }) {
  if (!phone && !email) return <span className="cell__empty">—</span>;
  return (
    <div className="cell">
      {phone && <div className="cell__title">{phone}</div>}
      {email && <div className={phone ? "cell__meta" : "cell__title"}>{email}</div>}
    </div>
  );
}

function OrderCell({ number, date }: { number: string | null; date: string | null }) {
  if (!number && !date) return <span className="cell__empty">—</span>;
  const formatted = formatRuDate(date);
  return (
    <div className="cell">
      <div className="cell__title">{number ?? "—"}</div>
      {formatted && <div className="cell__meta">от {formatted}</div>}
    </div>
  );
}

export function EmployeesPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("full_name");
  const [direction, setDirection] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState<EmployeeFormState | null>(null);

  const employees = useEmployees({ search, sort, direction, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE });
  const createEmployee = useCreateEmployee();
  const updateEmployee = useUpdateEmployee();
  const deleteEmployee = useDeleteEmployee();

  function sortBy(column: string) {
    if (sort === column) setDirection((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSort(column);
      setDirection("asc");
    }
    setPage(1);
  }

  async function submitForm() {
    if (!form) return;
    const payload = { ...form, order_number: form.order_number || null, order_date: form.order_date || null, email: form.email || null };
    if (form.id) await updateEmployee.mutateAsync({ id: form.id, payload });
    else await createEmployee.mutateAsync(payload);
    setForm(null);
  }

  const sortableColumns: { key: string; label: string }[] = [
    { key: "full_name", label: "ФИО" },
    { key: "position", label: "Должность" },
    { key: "department", label: "Подразделение" },
  ];

  return (
    <div className="page">
      <h1>Сотрудники</h1>
      <p className="muted">Реестр анкет сотрудников.</p>

      <div className="bar">
        <input
          type="search"
          placeholder="Поиск по ФИО или подразделению…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <div className="tools">
          <button type="button" className="btn btn--primary btn--small" onClick={() => setForm(EMPTY_FORM)}>
            Добавить сотрудника
          </button>
        </div>
      </div>

      {employees.isPending && <Loading label="Загружаем реестр…" />}
      {employees.isError && <ErrorState error={employees.error} onRetry={() => employees.refetch()} />}
      {employees.data && (
        <>
          <div className="table-wrap">
            <table>
              <colgroup>
                <col className="col-num" />
                <col style={{ width: "14%" }} />
                <col style={{ width: "15%" }} />
                <col style={{ width: "18%" }} />
                <col style={{ width: "15%" }} />
                <col style={{ width: "20%" }} />
                <col style={{ width: "12%" }} />
                <col className="col-actions" />
              </colgroup>
              <thead>
                <tr>
                  <th className="col-num">№</th>
                  {sortableColumns.map((column) => (
                    <th key={column.key}>
                      <button
                        type="button"
                        className={`th-sort${sort === column.key ? " th-sort--active" : ""}`}
                        onClick={() => sortBy(column.key)}
                      >
                        {column.label}
                        <span className="th-sort__arrow" aria-hidden={sort !== column.key}>
                          {sort === column.key ? (direction === "asc" ? "↑" : "↓") : "↕"}
                        </span>
                      </button>
                    </th>
                  ))}
                  <th>Контакты</th>
                  <th>Руководитель</th>
                  <th>Приказ</th>
                  <th className="col-actions">
                    <span className="visually-hidden">Действия</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {employees.data.items.map((employee, index) => (
                  <tr key={employee.id} onClick={() => setForm(toForm(employee))} className="row-clickable">
                    <td className="col-num">{(page - 1) * PAGE_SIZE + index + 1}</td>
                    <td>
                      <NameCell fullName={employee.full_name} />
                    </td>
                    <td>
                      <StackCell title={employee.position} />
                    </td>
                    <td>
                      <StackCell title={employee.department} />
                    </td>
                    <td>
                      <ContactsCell phone={employee.phone} email={employee.email} />
                    </td>
                    <td>
                      <StackCell
                        title={employee.manager_full_name}
                        meta={[employee.manager_position, employee.manager_phone].filter(Boolean).join(" · ") || null}
                      />
                    </td>
                    <td>
                      <OrderCell number={employee.order_number} date={employee.order_date} />
                    </td>
                    <td className="col-actions">
                      <button
                        type="button"
                        className="btn-ghost-danger"
                        onClick={(event) => {
                          event.stopPropagation();
                          if (confirm(`Удалить анкету «${employee.full_name}»?`)) deleteEmployee.mutate(employee.id);
                        }}
                      >
                        Удалить
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={PAGE_SIZE} total={employees.data.total} onPage={setPage} />
        </>
      )}

      <Dialog
        open={form !== null}
        title={form?.id ? "Редактировать сотрудника" : "Добавить сотрудника"}
        onClose={() => setForm(null)}
        onSubmit={submitForm}
        footer={
          <>
            <button type="button" className="btn btn--secondary" onClick={() => setForm(null)}>
              Отмена
            </button>
            <button type="submit" className="btn btn--primary" disabled={!form?.full_name}>
              Сохранить
            </button>
          </>
        }
      >
        {form && (
          <div className="cols">
            {(
              [
                ["full_name", "ФИО"],
                ["position", "Должность"],
                ["phone", "Телефон"],
                ["email", "Email"],
                ["department", "Подразделение"],
                ["manager_full_name", "ФИО руководителя"],
                ["manager_position", "Должность руководителя"],
                ["manager_phone", "Телефон руководителя"],
                ["order_number", "№ приказа"],
                ["order_date", "Дата приказа"],
              ] as const
            ).map(([key, label]) => (
              <div className="field-block" key={key}>
                <label>{label}</label>
                <input
                  type={key === "order_date" ? "date" : "text"}
                  value={form[key]}
                  onChange={(e) => setForm((prev) => (prev ? { ...prev, [key]: e.target.value } : prev))}
                />
              </div>
            ))}
          </div>
        )}
      </Dialog>
    </div>
  );
}
