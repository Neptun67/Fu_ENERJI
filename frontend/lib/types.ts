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
  /** Null once the vessel or berth has been deleted; the name below still holds. */
  ship_id: number | null;
  berth_id: number | null;
  /** Names as they were when the plan was generated. */
  ship_name: string;
  berth_name: string;
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
  ship_id: number | null;
  ship_name: string;
  reason: UnassignedReason;
  reason_message: string;
}
export interface Plan {
  id: number;
  created_at: string;
  buffer_min: number;
  total_waiting_min: number;
  /** Set when a ship or berth the plan used was deleted. The plan itself is
   *  never rewritten - this only marks that it no longer matches current data. */
  stale_at: string | null;
  stale_reason: string | null;
  assignments: Assignment[];
  unassigned_entries: UnassignedEntry[];
}
