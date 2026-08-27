// Conversions between API ISO (UTC) and <input type="datetime-local">.
// For simplicity every time is treated as UTC and labelled as UTC in the UI.

export function isoToInput(iso: string): string {
  // "2026-08-26T08:00:00Z" -> "2026-08-26T08:00"
  return iso.slice(0, 16);
}

export function inputToIso(value: string): string {
  // "2026-08-26T08:00" -> "2026-08-26T08:00:00Z"
  return value.length === 16 ? `${value}:00Z` : value;
}

function toDate(iso: string): Date {
  const hasTz = /[Zz]$|[+-]\d\d:?\d\d$/.test(iso);
  return new Date(hasTz ? iso : `${iso}Z`);
}

export function formatDateTime(iso: string): string {
  return (
    toDate(iso).toLocaleString("en-GB", {
      dateStyle: "short",
      timeStyle: "short",
      timeZone: "UTC",
    }) + " UTC"
  );
}

export function formatTime(iso: string): string {
  return toDate(iso).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

export function toMillis(iso: string): number {
  return toDate(iso).getTime();
}
