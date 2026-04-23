"use client";

import Link from "next/link";
import { useState, FormEvent } from "react";
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
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        // Simulate API call for the mockup
        setTimeout(() => {
            setIsSubmitting(false);
            setIsSubmitted(true);
        }, 1500);
    };

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
                                Whether you're a new user looking to learn more about Interview Standardiser, curious about how our platform structures preparation, or an existing user needing technical assistance, our team is here to help. Drop us a message and we'll get back to you!
                            </p>
                        </div>
                    </div>

                    {/* Right Form Component */}
                    <div className="bg-white/80 backdrop-blur-xl rounded-[2rem] border border-slate-200/50 shadow-[0_24px_48px_-12px_rgba(15,23,42,0.15)] ring-1 ring-black/5 p-8 sm:p-10">
                        {isSubmitted ? (
                            <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-center space-y-4 py-12">
                                <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-4 ring-8 ring-emerald-50">
                                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                    </svg>
                                </div>
                                <h3 className="text-2xl font-bold text-slate-800">Request Sent Successfully</h3>
                                <p className="text-slate-600 max-w-sm mx-auto">
                                    Thank you for reaching out. A support representative will review your message and contact you via email shortly.
                                </p>
                                <button
                                    onClick={() => setIsSubmitted(false)}
                                    className="mt-8 text-sm font-bold uppercase tracking-wider text-blue-600 hover:text-blue-700 transition"
                                >
                                    Send another message
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-800 mb-1">Send a Message</h2>
                                    <p className="text-sm text-slate-500 mb-6">Please fill out all mandatory fields below.</p>
                                </div>

                                <div className="space-y-5">
                                    <div className="space-y-2">
                                        <label htmlFor="name" className="block text-xs font-bold uppercase tracking-widest text-slate-500">
                                            Full Name <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            id="name"
                                            type="text"
                                            required
                                            placeholder="Jane Doe"
                                            className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3.5 text-sm font-medium text-slate-900 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 placeholder:text-slate-400 shadow-sm"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label htmlFor="email" className="block text-xs font-bold uppercase tracking-widest text-slate-500">
                                            Email Address <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            id="email"
                                            type="email"
                                            required
                                            placeholder="jane@university.edu"
                                            className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3.5 text-sm font-medium text-slate-900 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 placeholder:text-slate-400 shadow-sm"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label htmlFor="phone" className="block text-xs font-bold uppercase tracking-widest text-slate-500">
                                            Contact Number <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            id="phone"
                                            type="tel"
                                            required
                                            placeholder="+1 (555) 000-0000"
                                            className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3.5 text-sm font-medium text-slate-900 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 placeholder:text-slate-400 shadow-sm"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label htmlFor="message" className="block text-xs font-bold uppercase tracking-widest text-slate-500">
                                            How can we help?
                                        </label>
                                        <textarea
                                            id="message"
                                            rows={4}
                                            placeholder="Please describe the issue you are facing or the question you have..."
                                            className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3.5 text-sm font-medium text-slate-900 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 placeholder:text-slate-400 shadow-sm resize-none"
                                        />
                                    </div>
                                </div>

                                <div className="pt-2">
                                    <button
                                        type="submit"
                                        disabled={isSubmitting}
                                        className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4 text-sm font-bold text-white shadow-[0_8px_20px_rgba(37,99,235,0.25)] transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_12px_28px_rgba(37,99,235,0.35)] disabled:opacity-70 disabled:hover:scale-100"
                                    >
                                        {isSubmitting ? (
                                            <>
                                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                </svg>
                                                Sending request...
                                            </>
                                        ) : (
                                            "Submit Support Request"
                                        )}
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}