import "./LoadingSkeleton.css";

export default function LoadingSkeleton() {
  return (
    <div className="skeleton-root" aria-busy="true" aria-label="Loading analysis">
      <div className="skeleton-hero">
        <div className="sk sk-title" />
        <div className="sk sk-line short" />
      </div>
      <div className="skeleton-grid">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="sk sk-card" />
        ))}
      </div>
      <div className="sk sk-chart" />
      <div className="sk sk-block" />
    </div>
  );
}
