import { createBrowserRouter } from "react-router";

import { Layout } from "./components/Layout";
import { AdminOnly, HomeRedirect, NotFound, RouteError } from "./pages/misc";
import { EmployeesPage } from "./pages/admin/EmployeesPage";
import { RequestsLogPage } from "./pages/admin/RequestsLogPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RequestsPage } from "./pages/RequestsPage";

const basename = import.meta.env.BASE_URL.replace(/\/$/, "") || "/";

export const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <Layout />,
      errorElement: <RouteError />,
      children: [
        { index: true, element: <HomeRedirect /> },
        { path: "anketa", element: <ProfilePage /> },
        { path: "requests", element: <RequestsPage /> },
        { path: "admin/employees", element: <AdminOnly><EmployeesPage /></AdminOnly> },
        { path: "admin/requests", element: <AdminOnly><RequestsLogPage /></AdminOnly> },
        { path: "*", element: <NotFound /> },
      ],
    },
  ],
  { basename },
);
