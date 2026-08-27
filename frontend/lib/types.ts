export interface Ship {
  id: number;
  name: string;
  eta: string; // ISO (UTC)
  length_m: number;
  draft_m: number;
  handling_time_min: number;
  created_at: string;
  updated_at: string;
}
export interface ShipInput {
  name: string;
  eta: string;
  length_m: number;
  draft_m: number;
  handling_time_min: number;
}

export interface Berth {
  id: number;
  name: string;
  length_m: number;
  depth_m: number;
  created_at: string;
  updated_at: string;
}
export interface BerthInput {
  name: string;
  length_m: number;
  depth_m: number;
}

// --- plan ---
export interface Assignment {
  id: number;
  ship_id: number;
  berth_id: number;
  start_time: string;
  end_time: string;
  waiting_min: number;
}
export type UnassignedReason =
  | "no_suitable_length"
  | "no_suitable_depth"
  | "no_suitable_berth";
export interface UnassignedEntry {
  id: number;
  ship_id: number;
  reason: UnassignedReason;
  reason_message: string;
}
export interface Plan {
  id: number;
  created_at: string;
  buffer_min: number;
  total_waiting_min: number;
  assignments: Assignment[];
  unassigned_entries: UnassignedEntry[];
}
