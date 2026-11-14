
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function Pagination({
  page,
  totalPages,
  total,
  pageSize,
  onPageChange,
}) {
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <div className="cases-pagination">
      <p>
        Showing <strong>{start}–{end}</strong> of{" "}
        <strong>{total.toLocaleString("en-IN")}</strong> cases
      </p>

      <div className="pagination-actions">
        <button
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft size={16} />
          <span>Previous</span>
        </button>

        <span className="page-indicator">
          {page} / {Math.max(totalPages, 1)}
        </span>

        <button
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          <span>Next</span>
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
