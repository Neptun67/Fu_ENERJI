// API ISO (UTC) <-> <input type="datetime-local"> dönüşümleri.
// Sadelik için tüm saatler UTC olarak ele alınır ve arayüzde UTC etiketiyle gösterilir.

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
    toDate(iso).toLocaleString("tr-TR", {
      dateStyle: "short",
      timeStyle: "short",
      timeZone: "UTC",
    }) + " UTC"
  );
}

export function formatTime(iso: string): string {
  return toDate(iso).toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

export function toMillis(iso: string): number {
  return toDate(iso).getTime();
}
