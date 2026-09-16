import { useState } from "react";

import { useGeneratedRequests } from "../../api/hooks";
import { ErrorState, Loading, Pagination } from "../../components/states";

const PAGE_SIZE = 30;

function formatDate(value: string): string {
  return new Date(value).toLocaleString("ru-RU");
}

export function RequestsLogPage() {
  const [page, setPage] = useState(1);
  const log = useGeneratedRequests({ limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE });

  return (
    <div className="page">
      <h1>Журнал сформированных заявок</h1>
      <p className="muted">Кто, когда и какой документ сформировал — для аудита.</p>

      {log.isPending && <Loading label="Загружаем журнал…" />}
      {log.isError && <ErrorState error={log.error} onRetry={() => log.refetch()} />}
      {log.data && (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Когда</th>
                  <th>Сотрудник</th>
                  <th>Система</th>
                  <th>Действие</th>
                  <th>Файл</th>
                  <th>Сформировал</th>
                </tr>
              </thead>
              <tbody>
                {log.data.items.map((row) => (
                  <tr key={row.id}>
                    <td>{formatDate(row.created_at)}</td>
                    <td>{row.employee_full_name}</td>
                    <td>{row.system_id}</td>
                    <td>{row.action ?? "—"}</td>
                    <td>{row.file_name}</td>
                    <td>{row.generated_by}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={PAGE_SIZE} total={log.data.total} onPage={setPage} noun={["запись", "записи", "записей"]} />
        </>
      )}
    </div>
  );
}
