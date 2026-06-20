import SkeletonCard from "@/components/skeleton-card";

export default function Loading() {
  return (
    <div className="px-6 py-8" style={{ maxWidth: "768px", margin: "0 auto" }}>
      <div className="mb-6">
        <SkeletonCard lines={2} />
      </div>
      <SkeletonCard lines={8} />
    </div>
  );
}
