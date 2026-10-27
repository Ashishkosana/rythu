"use client";

import Link from "next/link";
import Icon from "@/components/ui/Icon";
import { ordered, useCalendar } from "@/lib/calendar";
import { CROP_LABEL } from "@/lib/cropLabels";
import { useFields, useToday, whenText } from "@/lib/fieldView";
import type { MyField } from "@/lib/fields";
import { pick, useLang, type Lang } from "@/lib/lang";

// The home screen's "what to do on my crop this week": tasks due now or within a week, across the
// farmer's fields. The full calendar is one tap away.
const PER_FIELD = 2;

export default function FieldsThisWeek() {
  const { lang } = useLang();
  const fields = useFields();
  const today = useToday();

  if (fields.length === 0) {
    return (
      <Link href="/field/" className="card tap flex items-center gap-3 p-4">
        <Icon name="calendar-days" size={28} className="shrink-0 text-brand-ink" />
        <span className="flex-1">
          <span className="block font-semibold">{pick(lang, "మీ పంట క్యాలెండర్", "Your crop calendar")}</span>
          <span className="block text-sm text-ink-secondary">
            {pick(lang, "విత్తిన తేదీ చెబితే ఏ రోజు ఏ పనో చూపిస్తాం", "Add your sowing date to see what to do when")}
          </span>
        </span>
        <Icon name="plus" size={22} className="shrink-0 text-brand-ink" />
      </Link>
    );
  }

  return (
    <section className="card p-4" aria-labelledby="this-week">
      <div className="flex items-center justify-between gap-2">
        <h2 id="this-week" className="flex items-center gap-2 font-bold">
          <Icon name="calendar-days" size={20} className="text-brand-ink" />
          {pick(lang, "ఈ వారం మీ పొలంలో", "This week on your fields")}
        </h2>
        <Link href="/field/" className="tap flex items-center text-sm font-semibold text-brand-ink">
          {pick(lang, "అన్నీ", "All")}
        </Link>
      </div>
      <ul className="mt-2 divide-y divide-line">
        {fields.map((f) => (
          <FieldNow key={f.id} field={f} today={today} lang={lang} />
        ))}
      </ul>
    </section>
  );
}

function FieldNow({ field, today, lang }: { field: MyField; today: string; lang: Lang }) {
  const q = useCalendar(field.crop, field.reference_date);
  const due = q.data ? ordered(q.data.tasks, today).filter((t) => t.when === "now" || t.when === "soon") : [];
  return (
    <li className="py-2">
      <p className="text-sm font-semibold text-ink-secondary">
        {CROP_LABEL[field.crop].emoji} {field.name}
      </p>
      {q.data && due.length === 0 && (
        <p className="text-sm">{pick(lang, "ఈ వారం ప్రత్యేక పని లేదు", "Nothing due this week")}</p>
      )}
      {due.slice(0, PER_FIELD).map(({ task, when }) => (
        <p key={task.id} className="mt-0.5">
          <span className="font-medium">{pick(lang, task.title_te, task.title_en)}</span>
          <span className="text-sm text-ink-secondary"> · {whenText(task, when, today, lang)}</span>
        </p>
      ))}
    </li>
  );
}
