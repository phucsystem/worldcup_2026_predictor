import SkeletonCard from "@/components/skeleton-card";

export default function Loading() {
  return (
    <div className="px-6 py-8" style={{ maxWidth: "960px", margin: "0 auto" }}>
      <div className="mb-6">
        <SkeletonCard lines={4} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  );
}
