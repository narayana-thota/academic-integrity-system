
import { Search, SlidersHorizontal, X } from "lucide-react";

export default function CaseFilters({
  search,
  setSearch,
  priority,
  setPriority,
  status,
  setStatus,
  onClear,
}) {
  const hasFilters = search || priority !== "ALL" || status !== "ALL";

  return (
    <section className="cases-toolbar">
      <div className="cases-search">
        <Search size={17} />
        <input
          type="search"
          placeholder="Search case ID, learner name or code..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        {search && (
          <button
            type="button"
            className="clear-search"
            onClick={() => setSearch("")}
            aria-label="Clear search"
          >
            <X size={15} />
          </button>
        )}
      </div>

      <div className="filter-control">
        <SlidersHorizontal size={16} />
        <select
          aria-label="Filter by priority"
          value={priority}
          onChange={(event) => setPriority(event.target.value)}
        >
          <option value="ALL">All priorities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <div className="filter-control">
        <select
          aria-label="Filter by status"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          <option value="ALL">All statuses</option>
          <option value="OPEN">Open</option>
          <option value="UNDER_REVIEW">Under review</option>
          <option value="CLOSED">Closed</option>
        </select>
      </div>

      {hasFilters && (
        <button className="clear-filters" onClick={onClear}>
          <X size={14} />
          Clear
        </button>
      )}
    </section>
  );
}
