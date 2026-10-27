"use client";

// My field: the farmer's fields and, for each, what to do when — from the one date they know
// (sowing, or transplanting for paddy and chilli). Tasks come from /v1/calendar, which restates the
// official PJTSAU / TNAU / ICAR / NIPHM guidance with its source; flagged tasks carry the AEO note.

import { useState } from "react";
import Icon from "@/components/ui/Icon";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { daysUntil, ordered, useCalendar, type CalendarTask, type TaskWhen } from "@/lib/calendar";
import { formatDay, useFields, useToday, whenText } from "@/lib/fieldView";
import { CROP_LABEL } from "@/lib/cropLabels";
import { MAX_FIELDS, MAX_NAME, TRANSPLANTED, newFieldId, removeField, upsertField, type MyField } from "@/lib/fields";
import { pick, useLang, type Lang } from "@/lib/lang";
import { CROPS, type Crop } from "@/lib/types";

function shift(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function referenceLabel(crop: Crop, lang: Lang): string {
  return TRANSPLANTED.has(crop) ? pick(lang, "నాట్లు వేసిన తేదీ", "Transplanting date") : pick(lang, "విత్తిన తేదీ", "Sowing date");
}

export default function FieldScreen() {
  const { lang } = useLang();
  const fields = useFields();
  const today = useToday();
  const [adding, setAdding] = useState(false);

  return (
    <main className="mx-auto min-h-dvh w-full max-w-md pb-28 text-ink">
      <ScreenHeader title={pick(lang, "నా పొలం", "My field")} subtitle={pick(lang, "ఏ పని, ఎప్పుడు", "What to do, and when")} />

      <div className="space-y-4 p-4 pt-6">
        {fields.length === 0 && !adding && (
          <section className="card p-5 text-center">
            <Icon name="calendar-days" size={36} className="mx-auto text-brand-ink" />
            <p className="mt-2 font-semibold">
              {pick(lang, "మీ పంట, విత్తిన తేదీ చెప్పండి", "Tell us your crop and its sowing date")}
            </p>
            <p className="mt-1 text-sm text-ink-secondary">
              {pick(
                lang,
                "ఎరువు, తనిఖీ పనులు ఏ రోజు చేయాలో చూపిస్తాం.",
                "We'll show which day each fertilizer and pest-check task falls on.",
              )}
            </p>
          </section>
        )}

        {fields.map((f) => (
          <FieldCard key={f.id} field={f} today={today} lang={lang} />
        ))}

        {adding ? (
          <FieldForm today={today} lang={lang} index={fields.length + 1} onDone={() => setAdding(false)} />
        ) : (
          fields.length < MAX_FIELDS && (
            <button
              onClick={() => setAdding(true)}
              className="tap flex w-full items-center justify-center gap-2 rounded-2xl bg-brand px-4 py-3 font-semibold text-white"
            >
              <Icon name="plus" size={20} /> {pick(lang, "పొలం చేర్చండి", "Add a field")}
            </button>
          )
        )}

        <p className="px-2 text-center text-sm text-ink-secondary">
          {pick(
            lang,
            "PJTSAU / TNAU / ICAR సాధారణ సూచనలు. మోతాదులు మీ Soil Health Card, AEO తో నిర్ధారించుకోండి.",
            "General guidance from PJTSAU / TNAU / ICAR. Confirm doses with your Soil Health Card and AEO.",
          )}
        </p>
      </div>
    </main>
  );
}

function FieldForm({ today, lang, index, onDone }: { today: string; lang: Lang; index: number; onDone: () => void }) {
  const [name, setName] = useState(pick(lang, `పొలం ${index}`, `Field ${index}`));
  const [crop, setCrop] = useState<Crop>("cotton");
  const [date, setDate] = useState(today);
  const min = shift(today, -400);
  const max = shift(today, 60);
  const dateOk = date >= min && date <= max;

  return (
    <form
      className="card space-y-4 p-4"
      aria-labelledby="new-field"
      onSubmit={(e) => {
        e.preventDefault();
        if (!dateOk || !name.trim()) return;
        upsertField({ id: newFieldId(), name, crop, reference_date: date });
        onDone();
      }}
    >
      <h2 id="new-field" className="text-lg font-bold">
        {pick(lang, "కొత్త పొలం", "New field")}
      </h2>
      <label className="block">
        <span className="text-sm font-medium text-ink-secondary">{pick(lang, "పేరు", "Name")}</span>
        <input
          value={name}
          maxLength={MAX_NAME}
          onChange={(e) => setName(e.target.value)}
          className="tap mt-1 w-full rounded-xl border border-line-strong px-4 py-2.5 outline-none focus:border-brand"
        />
      </label>
      <fieldset>
        <legend className="text-sm font-medium text-ink-secondary">{pick(lang, "పంట", "Crop")}</legend>
        <div className="mt-1 flex flex-wrap gap-2">
          {CROPS.map((c) => (
            <button
              key={c}
              type="button"
              aria-pressed={crop === c}
              onClick={() => setCrop(c)}
              className={`tap flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium ${
                crop === c ? "bg-brand text-white" : "bg-surface-sunken text-ink"
              }`}
            >
              {CROP_LABEL[c].emoji} {CROP_LABEL[c][lang]}
            </button>
          ))}
        </div>
      </fieldset>
      <label className="block">
        <span className="text-sm font-medium text-ink-secondary">{referenceLabel(crop, lang)}</span>
        <input
          type="date"
          value={date}
          min={min}
          max={max}
          required
          onChange={(e) => setDate(e.target.value)}
          className="tap mt-1 w-full rounded-xl border border-line-strong px-4 py-2.5 outline-none focus:border-brand"
        />
      </label>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!dateOk || !name.trim()}
          className="tap flex-1 rounded-xl bg-brand px-4 py-2.5 font-semibold text-white disabled:opacity-50"
        >
          {pick(lang, "సేవ్ చేయండి", "Save")}
        </button>
        <button
          type="button"
          onClick={onDone}
          className="tap flex-1 rounded-xl border border-line-strong bg-surface-raised px-4 py-2.5 font-semibold"
        >
          {pick(lang, "వద్దు", "Cancel")}
        </button>
      </div>
    </form>
  );
}

const GROUPS: { when: TaskWhen; te: string; en: string }[] = [
  { when: "now", te: "ఇప్పుడు", en: "Now" },
  { when: "soon", te: "ఈ వారం", en: "This week" },
  { when: "later", te: "తర్వాత", en: "Later" },
  { when: "stage", te: "దశను బట్టి", en: "By crop stage" },
];

function FieldCard({ field, today, lang }: { field: MyField; today: string; lang: Lang }) {
  const q = useCalendar(field.crop, field.reference_date);
  const [confirm, setConfirm] = useState(false);
  const day = -daysUntil(field.reference_date, today);
  const label = CROP_LABEL[field.crop];
  const tasks = q.data ? ordered(q.data.tasks, today) : [];
  const done = tasks.filter((t) => t.when === "done");

  return (
    <section className="card p-4" aria-labelledby={`field-${field.id}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 id={`field-${field.id}`} className="text-lg font-bold">
            {label.emoji} {field.name}
          </h2>
          <p className="text-sm text-ink-secondary">
            {label[lang]} · {referenceLabel(field.crop, lang)} {formatDay(field.reference_date, lang)}
            {day >= 0 && ` · ${pick(lang, `${day}వ రోజు`, `day ${day}`)}`}
          </p>
        </div>
        <button
          onClick={() => setConfirm((v) => !v)}
          aria-expanded={confirm}
          aria-label={pick(lang, `${field.name} తొలగించు`, `Remove ${field.name}`)}
          className="tap flex shrink-0 items-center justify-center rounded-xl text-ink-secondary"
        >
          <Icon name="trash" size={20} />
        </button>
      </div>

      {confirm && (
        <div role="alertdialog" aria-label={pick(lang, "తొలగించాలా?", "Remove?")} className="mt-3 flex items-center gap-2 rounded-xl bg-act-bg p-3">
          <p className="flex-1 text-sm font-semibold text-act-fg">{pick(lang, "ఈ పొలం తొలగించాలా?", "Remove this field?")}</p>
          <button onClick={() => removeField(field.id)} className="tap rounded-lg bg-act-fg px-3 text-sm font-semibold text-white">
            {pick(lang, "అవును", "Yes")}
          </button>
          <button onClick={() => setConfirm(false)} className="tap rounded-lg border border-line-strong bg-surface-raised px-3 text-sm font-semibold">
            {pick(lang, "వద్దు", "No")}
          </button>
        </div>
      )}

      {q.isPending && <div className="mt-4 h-24 animate-pulse rounded-xl bg-surface-sunken motion-reduce:animate-none" />}
      {q.isError && !q.data && (
        <p role="status" className="mt-4 rounded-xl bg-caution-bg px-3 py-2 text-sm text-caution-fg">
          {pick(lang, "క్యాలెండర్ రాలేదు — ఇంటర్నెట్ ఉన్నప్పుడు మళ్లీ చూడండి.", "Couldn't load the calendar — try again with internet.")}
        </p>
      )}

      {GROUPS.map((g) => {
        const items = tasks.filter((t) => t.when === g.when);
        if (items.length === 0) return null;
        return (
          <div key={g.when} className="mt-4">
            <h3 className="text-sm font-bold text-ink-secondary">{pick(lang, g.te, g.en)}</h3>
            <ul className="mt-2 space-y-2">
              {items.map(({ task, when }) => (
                <TaskRow key={task.id} task={task} when={when} today={today} lang={lang} />
              ))}
            </ul>
          </div>
        );
      })}

      {done.length > 0 && (
        <details className="mt-4">
          <summary className="tap flex cursor-pointer items-center text-sm font-bold text-ink-secondary">
            {pick(lang, `అయిపోయినవి (${done.length})`, `Done (${done.length})`)}
          </summary>
          <ul className="mt-2 space-y-2">
            {done.map(({ task, when }) => (
              <TaskRow key={task.id} task={task} when={when} today={today} lang={lang} />
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

const KIND_STYLE: Record<CalendarTask["kind"], string> = {
  fertilizer: "bg-success-bg text-success-fg",
  scout: "bg-caution-bg text-caution-fg",
  weeds: "bg-info-bg text-info-fg",
  prepare: "bg-neutral-bg text-neutral-fg",
};

const KIND_LABEL: Record<CalendarTask["kind"], { te: string; en: string }> = {
  fertilizer: { te: "ఎరువు", en: "Fertilizer" },
  scout: { te: "తనిఖీ", en: "Check" },
  weeds: { te: "కలుపు", en: "Weeds" },
  prepare: { te: "సిద్ధం", en: "Prepare" },
};

function TaskRow({ task, when, today, lang }: { task: CalendarTask; when: TaskWhen; today: string; lang: Lang }) {
  return (
    <li className={`rounded-xl p-3 ${when === "done" ? "bg-surface-sunken" : "bg-surface-raised ring-1 ring-line"}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-2 py-0.5 text-caption font-semibold ${KIND_STYLE[task.kind]}`}>
          {pick(lang, KIND_LABEL[task.kind].te, KIND_LABEL[task.kind].en)}
        </span>
        <span className="text-caption font-medium text-ink-secondary">{whenText(task, when, today, lang)}</span>
      </div>
      <p className="mt-1 font-semibold">{pick(lang, task.title_te, task.title_en)}</p>
      <p className="mt-0.5 text-sm text-ink-secondary">{pick(lang, task.detail_te, task.detail_en)}</p>
      {task.needs_verification && (
        <p className="mt-1.5 text-caption text-caution-fg">
          ⚠️ {pick(lang, "మీ AEO / Soil Health Card తో నిర్ధారించుకోండి", "Confirm with your AEO / Soil Health Card")}
        </p>
      )}
      <a href={task.source} target="_blank" rel="noopener noreferrer" className="hit-48 mt-1 inline-block text-caption text-brand-ink underline">
        {pick(lang, "మూలం", "Source")}
      </a>
    </li>
  );
}
