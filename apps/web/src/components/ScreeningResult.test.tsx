import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { SessionDetail } from "../lib/api";
import ScreeningResult from "./ScreeningResult";

function makeSession(overrides: Partial<SessionDetail> = {}): SessionDetail {
  return {
    id: "s1",
    status: "screened",
    resume_id: "r1",
    jd_id: "j1",
    company_profile_id: "faang-structured",
    fit_score: 0.85,
    started_at: null,
    completed_at: null,
    config_json: {
      competency_map: {
        competencies: [
          { name: "python", weight: 0.6, covered: true, coverage: 1.0, evidence: "python" },
          { name: "api design", weight: 0.4, covered: false, coverage: 0.1, evidence: null },
        ],
        coverage_score: 0.6,
      },
      fit: {
        fit_score: 0.85,
        proceed: true,
        rationale: "Strong dense match and good must-have coverage.",
        dense_similarity: 0.9,
        coverage: 0.8,
      },
      resume_summary: {},
      jd_summary: {},
    },
    ...overrides,
  };
}

describe("ScreeningResult", () => {
  it("renders fit score, band, archetype, competencies, and rationale", () => {
    render(<ScreeningResult session={makeSession()} />);

    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.getByTestId("fit-band")).toHaveTextContent("Strong");
    expect(screen.getByText("faang-structured")).toBeInTheDocument();
    expect(screen.getByText("python")).toBeInTheDocument();
    expect(screen.getByText("api design")).toBeInTheDocument();
    expect(
      screen.getByText(/good must-have coverage/i),
    ).toBeInTheDocument();
  });

  it("orders competencies by weight descending", () => {
    render(<ScreeningResult session={makeSession()} />);
    const items = screen.getAllByRole("listitem").map((li) => li.textContent);
    const pythonIdx = items.findIndex((t) => t?.includes("python"));
    const apiIdx = items.findIndex((t) => t?.includes("api design"));
    expect(pythonIdx).toBeLessThan(apiIdx);
  });

  it("shows a fallback when not yet screened", () => {
    render(<ScreeningResult session={makeSession({ config_json: null })} />);
    expect(screen.getByText(/not been screened yet/i)).toBeInTheDocument();
  });
});
