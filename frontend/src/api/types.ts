export interface FieldError {
  path: string;
  message: string;
}

export interface User {
  id: number;
  login: string;
  full_name: string;
  email: string | null;
  department: string | null;
  is_admin: boolean;
}

export interface DevUser {
  login: string;
  full_name: string;
  is_admin: boolean;
}

export interface Me {
  user: User;
  auth_mode: "dev" | "headers" | "jwt";
  dev_users: DevUser[] | null;
}

export type Office = "head_office" | "branch";

export interface Profile {
  id: number;
  user_id: number | null;
  updated_at: string;
  office: Office;
  full_name: string;
  position: string;
  phone: string;
  order_number: string | null;
  order_date: string | null;
  department: string;
  email: string | null;
  no_email: boolean;
  account_name: string | null;
  pkzi_name: string | null;
  manager_full_name: string;
  manager_position: string;
  manager_phone: string;
  vkd_action: string | null;
  vkd_rooms: string[];
  seid_role: string | null;
}

export type ProfileInput = Omit<Profile, "id" | "user_id" | "updated_at">;

export interface EmployeeAdmin extends Profile {}

export interface SystemChoice {
  field: string;
  options: string[];
}

export interface System {
  id: string;
  title: string;
  icon: string;
  desc: string;
  hl: boolean;
  ready: boolean;
  need: string[];
  choice: SystemChoice | null;
  instruction: string | null;
}

export interface EmployeePage {
  items: EmployeeAdmin[];
  total: number;
}

export interface GeneratedRequest {
  id: number;
  employee_profile_id: number;
  employee_full_name: string;
  system_id: string;
  action: string | null;
  file_name: string;
  generated_by: string;
  created_at: string;
}

export interface GeneratedRequestPage {
  items: GeneratedRequest[];
  total: number;
}
