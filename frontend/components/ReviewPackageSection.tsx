import { Card } from "@/components/ui/Card";
import { JsonSection } from "@/components/JsonSection";
import type { ReviewPackageSummary } from "@/lib/types";

export function ReviewPackageSection({
  reviewPackage,
  roleLabel,
}: {
  reviewPackage: ReviewPackageSummary;
  roleLabel: "admin" | "interviewer";
}) {
  const description =
    roleLabel === "admin"
      ? "Admin review artifact: raw PDF plus deterministic ROS Pages 1-3."
      : "Assigned review artifact: raw PDF plus deterministic ROS Pages 1-3.";

  return (
    <div className="space-y-6">
      <Card title="Review Package" description={description}>
        <div className="flex flex-col gap-3 text-sm text-muted md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <p>Canonical version {reviewPackage.canonical_version}</p>
            <p>Pages 1-3 are rendered from the persisted deterministic review package.</p>
          </div>
          <a
            className="inline-flex items-center justify-center rounded border border-line bg-surface px-4 py-2 text-sm text-ink transition hover:bg-stone-200"
            href={reviewPackage.pdf_url}
            rel="noreferrer"
            target="_blank"
          >
            Open source PDF
          </a>
        </div>
      </Card>

      <JsonSection
        title="ROS Page 1"
        description="Background profile"
        data={reviewPackage.pages_1_3.page_1_background_profile}
      />
      <JsonSection
        title="ROS Page 2"
        description="Academic and engagement"
        data={reviewPackage.pages_1_3.page_2_academic_and_engagement}
      />
      <JsonSection
        title="ROS Page 3"
        description="Essays"
        data={reviewPackage.pages_1_3.page_3_essays}
      />
    </div>
  );
}
