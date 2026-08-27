import Link from "next/link";

const sections = [
  {
    href: "/ships",
    title: "Ships",
    body: "Add incoming ships: arrival time, length, draft and handling time.",
  },
  {
    href: "/berths",
    title: "Berths",
    body: "Define your berths: length and depth capacity.",
  },
  {
    href: "/plan",
    title: "Plan",
    body: "Generate a rule-compliant berthing plan automatically and visualise it.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Berth planning
        </h1>
        <p className="mt-2 text-slate-600">
          Enter your ship and berth data, then generate a rule-compliant berthing
          plan that reduces total waiting time with a single click.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {sections.map((section) => (
          <Link
            key={section.href}
            href={section.href}
            className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow"
          >
            <h2 className="font-semibold text-slate-900 group-hover:text-teal-800">
              {section.title}
            </h2>
            <p className="mt-1.5 text-sm text-slate-600">{section.body}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
