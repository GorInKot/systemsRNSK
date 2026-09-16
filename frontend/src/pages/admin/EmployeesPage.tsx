import { useRef, useState } from "react";

import { ApiError, download } from "../../api/client";
import { useCreateEmployee, useDeleteEmployee, useEmployees, useImportEmployees, useUpdateEmployee } from "../../api/hooks";
import type { EmployeeAdmin } from "../../api/types";
import { Dialog } from "../../components/Dialog";
import { ErrorState, Loading, Pagination } from "../../components/states";

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

export function EmployeesPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("full_name");
  const [direction, setDirection] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState<EmployeeFormState | null>(null);
  const [message, setMessage] = useState("");
  const importInput = useRef<HTMLInputElement>(null);

  const employees = useEmployees({ search, sort, direction, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE });
  const createEmployee = useCreateEmployee();
  const updateEmployee = useUpdateEmployee();
  const deleteEmployee = useDeleteEmployee();
  const importEmployees = useImportEmployees();

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

  async function handleImportFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      if (!Array.isArray(parsed)) throw new Error("Файл должен содержать JSON-массив сотрудников.");
      const result = await importEmployees.mutateAsync(parsed);
      setMessage(`Импортировано: создано ${result.created}, обновлено ${result.updated}.`);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Не удалось прочитать файл импорта.");
    }
  }

  async function handleExport() {
    await download("/admin/employees/export", {}, "Сотрудники.xlsx");
  }

  const columns: { key: string; label: string; sortable?: boolean }[] = [
    { key: "full_name", label: "ФИО", sortable: true },
    { key: "position", label: "Должность", sortable: true },
    { key: "phone", label: "Телефон" },
    { key: "email", label: "Email" },
    { key: "department", label: "Подразделение", sortable: true },
    { key: "manager_full_name", label: "ФИО руководителя" },
    { key: "manager_position", label: "Должность руководителя" },
    { key: "manager_phone", label: "Телефон руководителя" },
    { key: "order_number", label: "№ приказа" },
    { key: "order_date", label: "Дата приказа" },
  ];

  return (
    <div className="page">
      <h1>Сотрудники</h1>
      <p className="muted">Реестр анкет сотрудников. Импорт/экспорт — JSON и Excel.</p>

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
          <button type="button" className="btn btn--secondary btn--small" onClick={() => importInput.current?.click()}>
            Импорт JSON
          </button>
          <input ref={importInput} type="file" accept="application/json" hidden onChange={handleImportFile} />
          <button type="button" className="btn btn--secondary btn--small" onClick={handleExport}>
            Экспорт
          </button>
          <button type="button" className="btn btn--primary btn--small" onClick={() => setForm(EMPTY_FORM)}>
            Добавить сотрудника
          </button>
        </div>
      </div>
      {message && <p className="muted">{message}</p>}

      {employees.isPending && <Loading label="Загружаем реестр…" />}
      {employees.isError && <ErrorState error={employees.error} onRetry={() => employees.refetch()} />}
      {employees.data && (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th className="col-num">№</th>
                  {columns.map((column) => (
                    <th key={column.key}>
                      {column.sortable ? (
                        <button type="button" className="th-sort" onClick={() => sortBy(column.key)}>
                          {column.label} {sort === column.key ? (direction === "asc" ? "↑" : "↓") : ""}
                        </button>
                      ) : (
                        column.label
                      )}
                    </th>
                  ))}
                  <th />
                </tr>
              </thead>
              <tbody>
                {employees.data.items.map((employee, index) => (
                  <tr key={employee.id} onClick={() => setForm(toForm(employee))} className="row-clickable">
                    <td className="col-num">{(page - 1) * PAGE_SIZE + index + 1}</td>
                    <td>{employee.full_name}</td>
                    <td>{employee.position}</td>
                    <td>{employee.phone}</td>
                    <td>{employee.email}</td>
                    <td>{employee.department}</td>
                    <td>{employee.manager_full_name}</td>
                    <td>{employee.manager_position}</td>
                    <td>{employee.manager_phone}</td>
                    <td>{employee.order_number}</td>
                    <td>{employee.order_date}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn--secondary btn--small"
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
