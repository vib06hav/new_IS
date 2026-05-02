"use client";

import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { Card } from "@/components/ui/Card";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-reports-space",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const THEMES = [
  "Technical Depth vs Practice",
  "Interdisciplinary Motivation",
];

export function Page4FocusAreaSandbox() {
  return (
    <div
      className={[
        spaceGrotesk.variable,
        plexSans.variable,
        "min-h-screen bg-[linear-gradient(180deg,#eef0f5_0%,#dfe3eb_22%,#d8dbe2_22%,#cfd5df_62%,#dfe3eb_62%,#eef0f5_100%)] text-[#111111]",
      ].join(" ")}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="min-h-screen bg-[#D8DBE2] text-[#111111]">
        <AdminDesignLabNavbar activeItem="Reports" />

        <main className="mx-auto max-w-[92rem] px-5 py-7 md:px-8 md:py-8">
          <div className="space-y-6">
            <section className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[linear-gradient(135deg,#c9d0dc_0%,#d8dbe2_40%,#ced4df_100%)] p-6">
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#5F6C86]">
                  <span className="inline-flex items-center gap-2 text-[#111111]">Design lab preview</span>
                </div>
                <div className="space-y-3">
                  <h1
                    className="max-w-4xl text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.6rem]"
                    style={{ fontFamily: "var(--font-reports-space)" }}
                  >
                    Page 4 focus area slice
                  </h1>
                  <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                    Detached mock of the real Page 4 layout using simplified copy for landing-page screenshots.
                  </p>
                </div>
              </div>
            </section>

            <Card
              title="Focus Areas"
              description="Themes, signals, and deeper interview openings for the reviewer."
              eyebrow={null}
            >
              <div className="grid gap-5 xl:grid-cols-[19rem_minmax(0,1fr)]">
                <section className="space-y-4">
                  <div className="space-y-2 xl:hidden">
                    <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Themes</p>
                    <label className="sr-only" htmlFor="sandbox-focus-theme-select">
                      Select theme
                    </label>
                    <select
                      id="sandbox-focus-theme-select"
                      className="w-full rounded-[1rem] border border-slate-200 bg-white/90 px-4 py-3 text-sm text-[color:var(--ink)] shadow-[0_10px_22px_rgba(15,23,42,0.05)]"
                      value={THEMES[0]}
                      readOnly
                    >
                      {THEMES.map((theme) => (
                        <option key={theme} value={theme}>
                          {theme}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="hidden space-y-3 xl:block">
                    <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Themes</p>
                    {THEMES.map((theme, index) => {
                      const active = index === 0;
                      return (
                        <button
                          key={theme}
                          type="button"
                          className={`block w-full rounded-[1.3rem] border p-4 text-left transition ${active
                              ? "border-blue-200 bg-[linear-gradient(145deg,rgba(239,246,255,0.98),rgba(255,255,255,0.94))] shadow-[0_18px_34px_rgba(15,23,42,0.08)]"
                              : "border-slate-200 bg-white/80 shadow-[0_16px_30px_rgba(15,23,42,0.06)] hover:bg-white/92"
                            }`}
                        >
                          <p className="text-sm font-semibold leading-6 text-[color:var(--ink)]">{theme}</p>
                        </button>
                      );
                    })}
                  </div>
                </section>

                <section className="space-y-4">
                  <article className="rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(145deg,rgba(255,255,255,0.96),rgba(239,246,255,0.88),rgba(255,255,255,0.9))] p-5 shadow-[0_18px_34px_rgba(15,23,42,0.08)]">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">
                          Interview Focus
                        </p>
                        <h3 className="text-2xl font-semibold tracking-[-0.03em] text-[color:var(--ink)]">
                          Technical Depth vs Practice
                        </h3>
                      </div>
                      <p className="text-sm leading-7 text-[color:var(--muted)]">
                        Strong interest in technology, but limited evidence of hands-on building.
                      </p>
                      <div className="rounded-[1rem] bg-[color:var(--accent-soft)] px-4 py-3 text-sm leading-7 text-[color:var(--ink)]">
                        <span className="font-semibold">Interview direction:</span>{" "}
                        Probe whether interest has translated into real projects or practical work.
                      </div>
                    </div>
                  </article>

                  <article className="rounded-[1.3rem] border border-slate-200 bg-white/82 p-5 shadow-[0_16px_30px_rgba(15,23,42,0.06)]">
                    <div className="space-y-2">
                      <p className="text-base font-semibold text-[color:var(--ink)]">Concept without execution</p>
                      <p className="text-sm leading-7 text-[color:var(--ink)]">
                        Talks about technology concepts confidently but lacks concrete examples of building or coding.
                      </p>
                    </div>
                  </article>
                </section>
              </div>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
