## Signals

**What they are:**

A signal is a unit of interview-relevant evidence extracted from a specific application. It is not an evaluation, not a conclusion, and not a question. It is the answer to a single question: *what in this application is specific enough, rich enough, and unresolved enough to be worth a skilled interviewer's time in a conversation?*

The key word is unresolved. A signal is not interesting because it shows something impressive or concerning. It is interesting because it shows something that the application cannot fully answer by itself — something where a conversation would produce information that would materially change how you understand this person. That unresolved quality is what makes it useful. Evidence that is fully legible from the application alone doesn't need to be surfaced in an interview. It's already answered.

**What a signal contains:**

The evidence anchor — the specific, named thing in the application that creates the opening. Not a category or a characterization. The actual thing: the specific claim in the essay, the specific activity or academic pattern, the specific data point. Named precisely enough that it could not describe any other applicant.

What it shows directly — what can be read from this evidence without inference. Factual, not evaluative. This is the part that is already answered.

What it leaves open — the specific thing this evidence cannot tell you that a conversation could. This is the load-bearing part. It should be stated as a genuine unknown, not as a suspected weakness or a gap to be filled. The unknown should be the kind that would produce different interpretations of the applicant depending on how it resolved. If knowing the answer wouldn't change your understanding of the person, it's not a real unknown and the signal isn't earning its place.

**What a signal is not:**

It is not a tension or a gap. Those are evaluative frames — they position the interviewer as an auditor checking whether the application holds together. A signal doesn't audit. It identifies where the evidence is rich and where it runs out, without making a judgment about what that means.

It is not a hook or a proto-question. The signal's job ends at the unresolved element. How that unknown gets converted into a question — what framing, what angle, what conversational approach — is Call 2's job. If Call 1 pre-shapes the unknown into a directional hook, it contaminates the input. Call 2 will either be constrained by the framing it inherited or will have to discard it and reason independently, making it wasted work.

It is not dimension-mapped. The three interviewer dimensions — or whatever evaluation criteria exist — belong to Call 2. Call 1's job is to find what is genuinely interview-worthy in this application. Whether a given signal speaks to grit or tech genuineness or problem solving is a downstream interpretation. If Call 1 pre-assigns dimensions, it may discard evidence that doesn't fit neatly into a named category but would generate a sharper question than evidence that does. The selection logic should be: is this specific, is it rich, is it genuinely unresolved. Not: which dimension does this serve.

**How many:**

However many the application actually supports. Not a fixed number. The floor-and-ceiling rule in the current prompt exists because the prompt is trying to ensure coverage and depth. If signals are defined correctly — specific, rich, genuinely unresolved — the number that emerges is the right number. An application with one truly rich piece of evidence should produce one signal. Forcing three produces padding. An application with five genuinely distinct unresolved elements should produce five. The number is a symptom of the application's interview-worthiness, not a parameter to set.

**What they're for:**

Signals are the atomized inputs Call 2 needs to generate targeted questions. They hand off structured, precise, unconclusive evidence so that Call 2 can apply its own reasoning — its knowledge of the evaluation criteria, its sense of what a good question looks like, its understanding of what the interviewer needs to walk in knowing — without having to re-read the application. The signal is complete when it contains everything Call 2 needs to work with this piece of evidence and nothing Call 2 should be doing itself.

---

## Theme

**What it is:**

The theme is the answer to a different and higher-order question: *who is this person as an interview subject, and what does their interview fundamentally need to resolve?*

It is not a summary of the signals. It is not a cross-dimensional pattern-find. It is a characterization of what all the signals together reveal about this applicant that no individual signal reveals alone. The theme emerges from synthesis — from seeing the full signal set simultaneously and asking what they collectively say about this person at the level of the whole, not the parts.

The distinction matters. Three signals might each be individually interesting and well-grounded. But together they might point at a single underlying question about this person — something about the relationship between their stated direction and their demonstrated self, or between their evident capability and their evident self-awareness, or between the person they're presenting and the person the record actually shows. That underlying question is the theme. It is what the interview is fundamentally about.

**What a theme contains:**

A single characterization of the applicant as an interview subject. Specific to this person — not a type or a category. It should be the kind of statement that, if you handed it to a skilled interviewer with no other context, they would immediately understand what the conversation needs to do.

The governing frame it creates for questions. The theme is not just a description — it is a constraint. Questions generated in service of a theme should be coherent with each other. They should feel like they belong to the same interview, not like three independently targeted probes that happen to be aimed at the same person. The theme is what produces that coherence.

**What a theme is not:**

It is not an evaluation or a conclusion about the applicant. It does not say this person is strong or weak, deep or shallow, genuine or performing. It characterizes what is unresolved about them as an interview subject — what the conversation needs to surface, not what the interviewer should conclude.

It is not a synthesis of tensions or gaps. The current prompt produces something like a theme by identifying the most prominent mismatch in the application. That's still auditing. A real theme might emerge from coherent signals — three pieces of evidence that all point at the same underlying unknown — rather than from a tension between them.

**How it's used:**

The theme gives Call 2 its governing frame before it generates any questions. It tells Call 2 what the interview is about at the level of this whole person. Questions should serve that frame — they should be individually targeted enough to probe specific evidence, but collectively coherent enough that they're all working toward the same thing. Without a theme, Call 2 produces three unrelated questions. With a theme, it produces three questions that feel like they belong to a single, purposeful conversation.

---

## The relationship between them

Signals and theme are not parallel outputs. They are sequential in their logic even if they're produced in the same call.

Signals come first because they are the evidence layer. They are extracted from the application independently — each one earns its place on its own merits, not because of how it relates to the others.

The theme comes second because it requires seeing all the signals together. It is the synthesis layer. It can only be written once you know what the full signal set is, because it characterizes what they collectively reveal.

Call 2 uses both but differently. It uses signals as targeting inputs — each signal tells it where to aim and what remains open. It uses the theme as a coherence constraint — the theme tells it what the interview is fundamentally about, so the questions it generates are working together rather than independently.

The test for whether the signals and theme are doing their jobs: if Call 2 receives them and can generate questions that are simultaneously specific to this applicant, targeted at genuine unknowns, and coherent with each other — without re-reading the application — then Call 1 has done its job correctly. If Call 2 has to infer, synthesize, or re-interpret, Call 1 has either under-delivered or over-interpreted.