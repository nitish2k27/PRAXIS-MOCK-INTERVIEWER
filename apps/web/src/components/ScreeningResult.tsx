import type { SessionDetail } from "../lib/api";
import { fitBand } from "../lib/api";

const BAND_STYLES: Record<string, string> = {
  Strong: "bg-green-100 text-green-800",
  Promising: "bg-emerald-100 text-emerald-800",
  Mixed: "bg-amber-100 text-amber-800",
  Weak: "bg-red-100 text-red-800",
};

const TOP_N = 5;

export default function ScreeningResult({ session }: { session: SessionDetail }) {
  const config = session.config_json;
  if (!config) {
    return (
      <div className="text-slate-500">
        This session has not been screened yet.
      </div>
    );
  }

  const score = config.fit.fit_score;
  const band = fitBand(score);
  const pct = Math.round(score * 100);
  const topCompetencies = [...config.competency_map.competencies]
    .sort((a, b) => b.weight - a.weight)
    .slice(0, TOP_N);

  return (
    <div className="space-y-6">
      <section className="flex items-center gap-4">
        <div>
          <div className="text-4xl font-semibold tabular-nums">{pct}</div>
          <div className="text-xs text-slate-500">fit score</div>
        </div>
        <span
          className={`px-2 py-1 rounded text-sm font-medium ${BAND_STYLES[band]}`}
          data-testid="fit-band"
        >
          {band}
        </span>
        <div className="ml-auto text-right">
          <div className="text-xs text-slate-500">Company archetype</div>
          <div className="font-medium">{session.company_profile_id ?? "—"}</div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-medium mb-2">Top weighted competencies</h3>
        {topCompetencies.length === 0 ? (
          <div className="text-sm text-slate-500">No competencies derived.</div>
        ) : (
          <ul className="space-y-1">
            {topCompetencies.map((c) => (
              <li
                key={c.name}
                className="flex items-center justify-between text-sm border-b py-1"
              >
                <span className="flex items-center gap-2">
                  <span
                    className={c.covered ? "text-green-600" : "text-slate-400"}
                    aria-label={c.covered ? "covered" : "not covered"}
                  >
                    {c.covered ? "✓" : "✗"}
                  </span>
                  {c.name}
                </span>
                <span className="text-slate-500 tabular-nums">
                  {Math.round(c.weight * 100)}%
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3 className="text-sm font-medium mb-1">Rationale</h3>
        <p className="text-sm text-slate-700">{config.fit.rationale}</p>
      </section>
    </div>
  );
}
