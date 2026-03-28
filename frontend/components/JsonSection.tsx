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
      <div className="overflow-x-auto rounded-[1.2rem] border border-[color:var(--line)] bg-white/80 p-4 text-sm text-[color:var(--ink)] shadow-[var(--card-shadow-soft)]">
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </Card>
  );
}
