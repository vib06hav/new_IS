"use client";

import Link from "next/link";
import { Libre_Franklin, IBM_Plex_Sans } from "next/font/google";

const libreFranklin = Libre_Franklin({
    subsets: ["latin"],
    weight: ["900"],
    variable: "--font-display",
    display: "swap",
});

const ibmPlexSans = IBM_Plex_Sans({
    subsets: ["latin"],
    weight: ["400", "500", "600"],
    variable: "--font-body",
    display: "swap",
});

export default function SupportPage() {
    return (
        <div className={`min-h-screen bg-slate-50 flex flex-col ${libreFranklin.variable} ${ibmPlexSans.variable} font-sans`}>
            {/* Background Decorators */}
            <div className="pointer-events-none fixed inset-0 overflow-hidden">
                <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-blue-100/40 blur-[120px]" />
                <div className="absolute top-[40%] -right-[15%] w-[60%] h-[60%] rounded-full bg-indigo-100/40 blur-[100px]" />
            </div>

            <header className="relative z-10 bg-white/70 backdrop-blur-md border-b border-slate-200/60 sticky top-0 px-6 py-4 flex items-center justify-between">
                <Link href="/" className="flex items-center space-x-2 group">
                    <div className="relative w-10 h-10 flex items-center justify-center bg-blue-50 rounded-lg border border-blue-100 transition-colors group-hover:bg-blue-100/80">
                        <svg
                            className="w-5 h-5 text-blue-700"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
                        </svg>
                    </div>
                    <span className="text-sm font-bold text-slate-600 group-hover:text-slate-900 uppercase tracking-widest transition-colors">
                        Back to Home
                    </span>
                </Link>
            </header>

            <main className="relative z-10 flex-1 flex items-center justify-center p-6 sm:p-12">
                <div className="w-full max-w-5xl grid lg:grid-cols-2 gap-12 lg:gap-20 items-start">

                    {/* Left Text Detail */}
                    <div className="space-y-8 pt-8">
                        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-indigo-200 bg-indigo-50/70">
                            <div className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-pulse" />
                            <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-900">
                                Priority Help Desk
                            </span>
                        </div>

                        <div>
                            <h1
                                className="text-4xl sm:text-5xl font-black text-slate-800 tracking-tight leading-[1.1] mb-6"
                                style={{ fontFamily: "var(--font-display)" }}
                            >
                                How can we support your{" "}
                                <span className="text-blue-700">interview process?</span>
                            </h1>
                            <p className="text-lg text-slate-600 leading-relaxed font-body">
                                Whether you&apos;re exploring Interview Standardiser for your team or you&apos;re already using the platform and need help, choose the path that fits your request and we&apos;ll collect the right details.
                            </p>
                        </div>
                    </div>

                    {/* Right Form Component */}
                    <div className="bg-white/80 backdrop-blur-xl rounded-[2rem] border border-slate-200/50 shadow-[0_24px_48px_-12px_rgba(15,23,42,0.15)] ring-1 ring-black/5 p-8 sm:p-10">
                        <div className="space-y-6">
                            <div>
                                <h2 className="text-xl font-bold text-slate-800 mb-1">Choose a support path</h2>
                                <p className="text-sm text-slate-500 mb-6">
                                    Opens a short Google Form so we can contact you.
                                </p>
                            </div>

                            <div className="space-y-4">
                                <a
                                    href="https://docs.google.com/forms/d/e/1FAIpQLSfN5Y-j5zO8M8AEkjMAi-8ln4hz2vlx907BJ3L4kbSfSCP9GA/viewform?usp=publish-editor"
                                    target="_blank"
                                    rel="noreferrer"
                                    className="group block rounded-[1.5rem] border border-slate-200 bg-white/70 p-5 shadow-sm transition hover:border-blue-200 hover:bg-white hover:shadow-[0_18px_36px_rgba(37,99,235,0.12)]"
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="space-y-2">
                                            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-blue-700">New teams</p>
                                            <h3 className="text-lg font-bold text-slate-900">Request a demo</h3>
                                            <p className="text-sm leading-6 text-slate-600">
                                                Learn how Interview Standardiser can support your interview workflow and share what you&apos;re evaluating.
                                            </p>
                                        </div>
                                        <ArrowIcon />
                                    </div>
                                </a>

                                <a
                                    href="https://docs.google.com/forms/d/e/1FAIpQLSfl3CNPL9H_nqFSIKDnWjEWgEmI5AuioO7eGdAWaJLCGAcA1Q/viewform?usp=publish-editor"
                                    target="_blank"
                                    rel="noreferrer"
                                    className="group block rounded-[1.5rem] border border-slate-200 bg-white/70 p-5 shadow-sm transition hover:border-indigo-200 hover:bg-white hover:shadow-[0_18px_36px_rgba(79,70,229,0.12)]"
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="space-y-2">
                                            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-indigo-700">Current users</p>
                                            <h3 className="text-lg font-bold text-slate-900">Existing user support</h3>
                                            <p className="text-sm leading-6 text-slate-600">
                                                Get help with workflow issues, questions, or anything blocking your team inside the platform.
                                            </p>
                                        </div>
                                        <ArrowIcon />
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

function ArrowIcon() {
    return (
        <svg
            className="mt-1 h-5 w-5 shrink-0 text-slate-400 transition group-hover:text-blue-700"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
        >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
        </svg>
    );
}
