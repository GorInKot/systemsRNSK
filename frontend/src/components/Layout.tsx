import { Link, NavLink, Outlet } from "react-router";

import { getDevUser, setDevUser } from "../api/client";
import { useMe } from "../api/hooks";
import { ErrorState, Loading } from "./states";

export function Layout() {
  const me = useMe();

  if (me.isPending) return <Loading label="Загружаем систему заявок…" />;
  if (me.isError)
    return (
      <div className="page page--narrow">
        <ErrorState error={me.error} onRetry={() => me.refetch()} />
      </div>
    );

  const { user, dev_users: devUsers } = me.data;
  const links = [
    { to: "/anketa", label: "Анкета", end: true },
    { to: "/requests", label: "Заявки", end: true },
    ...(user.is_admin
      ? [
          { to: "/admin/employees", label: "Сотрудники", end: true },
          { to: "/admin/requests", label: "Журнал заявок", end: true },
        ]
      : []),
  ];

  return (
    <>
      <header className="topbar">
        <div className="topbar__inner">
          <Link to="/" className="topbar__title">
            Заявки на доступы
          </Link>
          <nav className="topbar__nav" aria-label="Разделы">
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} end={link.end} className="topbar__link">
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="topbar__side">
            {devUsers ? (
              <label className="dev-switch">
                <span className="dev-switch__tag">Тест</span>
                <span className="visually-hidden">Войти как</span>
                <select
                  value={getDevUser() ?? user.login}
                  onChange={(event) => {
                    setDevUser(event.target.value);
                    window.location.assign(import.meta.env.BASE_URL);
                  }}
                >
                  {devUsers.map((devUser) => (
                    <option key={devUser.login} value={devUser.login}>
                      {devUser.full_name}
                      {devUser.is_admin ? " — администратор" : ""}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <span>{user.full_name}</span>
            )}
          </div>
        </div>
      </header>
      <main id="main">
        <Outlet />
      </main>
    </>
  );
}
