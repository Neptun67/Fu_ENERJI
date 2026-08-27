import type { Berth, BerthInput, Plan, Ship, ShipInput } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store", // operations tool: always show current data
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* if the body is not JSON, keep statusText */
    }
    throw new ApiError(res.status, String(detail));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// --- ships ---
export const listShips = () => request<Ship[]>("/ships");
export const createShip = (data: ShipInput) =>
  request<Ship>("/ships", { method: "POST", body: JSON.stringify(data) });
export const updateShip = (id: number, data: Partial<ShipInput>) =>
  request<Ship>(`/ships/${id}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteShip = (id: number) =>
  request<void>(`/ships/${id}`, { method: "DELETE" });

// --- berths ---
export const listBerths = () => request<Berth[]>("/berths");
export const createBerth = (data: BerthInput) =>
  request<Berth>("/berths", { method: "POST", body: JSON.stringify(data) });
export const updateBerth = (id: number, data: Partial<BerthInput>) =>
  request<Berth>(`/berths/${id}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteBerth = (id: number) =>
  request<void>(`/berths/${id}`, { method: "DELETE" });

// --- plans ---
export const listPlans = () => request<Plan[]>("/plans");
export const getPlan = (id: number) => request<Plan>(`/plans/${id}`);
export const generatePlan = (bufferMin?: number) =>
  request<Plan>("/plans", {
    method: "POST",
    body: JSON.stringify(bufferMin != null ? { buffer_min: bufferMin } : {}),
  });
export const deletePlan = (id: number) =>
  request<void>(`/plans/${id}`, { method: "DELETE" });
