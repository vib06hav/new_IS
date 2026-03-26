import { Card } from "@/components/ui/Card";

export function JsonSection({
  title,
  description,
  data,
}: {
  title: string;
  description?: string;
  data: unknown;
}) {
  return (
    <Card title={title} description={description}>
      <div className="overflow-x-auto rounded border border-line bg-surface p-4 text-sm text-ink">
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </Card>
  );
}
