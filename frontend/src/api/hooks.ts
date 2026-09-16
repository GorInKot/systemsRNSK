import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import type {
  EmployeeAdmin,
  EmployeeImportResult,
  EmployeePage,
  GeneratedRequestPage,
  Me,
  Profile,
  ProfileInput,
  System,
} from "./types";

export function useMe() {
  return useQuery({ queryKey: ["me"], queryFn: () => api<Me>("/me"), staleTime: 30_000 });
}

export function useProfile() {
  return useQuery({ queryKey: ["profile"], queryFn: () => api<Profile>("/profile") });
}

export function useSaveProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileInput) => api<Profile>("/profile", { method: "PUT", body: payload }),
    onSuccess: (profile) => {
      queryClient.setQueryData(["profile"], profile);
      queryClient.invalidateQueries({ queryKey: ["systems"] });
    },
  });
}

export function useSystems() {
  return useQuery({ queryKey: ["systems"], queryFn: () => api<System[]>("/systems"), staleTime: Infinity });
}

export interface EmployeeListParams {
  search: string;
  sort: string;
  direction: "asc" | "desc";
  limit: number;
  offset: number;
}

export function useEmployees(params: EmployeeListParams) {
  return useQuery({
    queryKey: ["admin", "employees", params],
    queryFn: () =>
      api<EmployeePage>("/admin/employees", {
        query: { search: params.search, sort: params.sort, direction: params.direction, limit: params.limit, offset: params.offset },
      }),
  });
}

export function useCreateEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<ProfileInput> & { full_name: string }) => api<EmployeeAdmin>("/admin/employees", { method: "POST", body: payload }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "employees"] }),
  });
}

export function useUpdateEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<ProfileInput> }) =>
      api<EmployeeAdmin>(`/admin/employees/${id}`, { method: "PUT", body: payload }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "employees"] }),
  });
}

export function useDeleteEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api<void>(`/admin/employees/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "employees"] }),
  });
}

export function useImportEmployees() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: unknown[]) => api<EmployeeImportResult>("/admin/employees/import", { method: "POST", body: payload }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "employees"] }),
  });
}

export function useGeneratedRequests(params: { employeeId?: number; systemId?: string; limit: number; offset: number }) {
  return useQuery({
    queryKey: ["admin", "requests", params],
    queryFn: () =>
      api<GeneratedRequestPage>("/admin/requests", {
        query: { employee_id: params.employeeId, system_id: params.systemId, limit: params.limit, offset: params.offset },
      }),
  });
}
