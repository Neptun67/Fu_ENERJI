import Link from "next/link";

const steps = [
  {
    href: "/ships",
    step: "1",
    title: "Ships",
    body: "Record incoming vessels: arrival time, length, draft and handling time.",
  },
  {
    href: "/berths",
    step: "2",
    title: "Berths",
    body: "Describe the quay: how long and how deep each berth is.",
  },
  {
    href: "/plan",
    step: "3",
    title: "Plan",
    body: "Generate a rule-compliant schedule and read it on the timeline.",
  },
];

const rules = [
  "One ship per berth at a time",
  "Ship length must fit the berth",
  "Ship draft must not exceed berth depth",
  "No ship is berthed before it arrives",
  "A manoeuvring buffer separates consecutive ships",
];

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="max-w-2xl pt-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sea-600">
          Port operations
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-sea-900 sm:text-4xl">
          Berth planning, without the guesswork
        </h1>
        <p className="mt-4 text-base leading-relaxed text-slate-600">
          Enter your vessels and your quay, then generate a schedule that respects every
          physical constraint and keeps total waiting time down. Ships that cannot be
          berthed are listed with the reason.
        </p>
        <div className="mt-7 flex flex-wrap items-center gap-3">
          <Link
            href="/plan"
            className="rounded-lg bg-sea-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-sea-800"
          >
            Generate a plan
          </Link>
          <Link
            href="/ships"
            className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-sea-800 transition-colors hover:bg-sea-50"
          >
            Manage ships
          </Link>
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-600">
          How it works
        </h2>
        <ol className="mt-4 grid gap-4 sm:grid-cols-3">
          {steps.map((s) => (
            <li key={s.href}>
              <Link
                href={s.href}
                className="group flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-sea-300 hover:shadow-md"
              >
                <span
                  aria-hidden="true"
                  className="grid h-7 w-7 place-items-center rounded-full bg-sea-100 text-xs font-bold text-sea-800"
                >
                  {s.step}
                </span>
                <span className="mt-3 font-semibold text-sea-900 group-hover:text-sea-700">
                  {s.title}
                </span>
                <span className="mt-1.5 text-sm leading-relaxed text-slate-600">
                  {s.body}
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-600">
          Rules the plan respects
        </h2>
        <ul className="mt-4 grid gap-x-8 gap-y-2.5 text-sm text-slate-700 sm:grid-cols-2">
          {rules.map((rule) => (
            <li key={rule} className="flex gap-2.5">
              <span
                aria-hidden="true"
                className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sea-400"
              />
              {rule}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
