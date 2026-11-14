
import { useCallback, useEffect, useState } from "react";
import { Search, RefreshCw, ChevronLeft, ChevronRight, X, ClipboardList } from "lucide-react";
import api from "../services/api";
import "../styles/audit-history.css";

const PAGE_SIZE = 20;

const formatDate = (value) => {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const parseEventData = (value) => {
  if (!value) return {};

  if (typeof value === "object") return value;

  try {
    return JSON.parse(value);
  } catch {
    return { raw_value: value };
  }
};

const formatLabel = (value) =>
  String(value || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());

function EventBadge({ value }) {
  const normalized = String(value || "").toLowerCase();

  let className = "audit-badge";

  if (normalized.includes("reviewer")) className += " reviewer";
  else if (normalized.includes("system")) className += " system";
  else if (normalized.includes("appeal")) className += " appeal";
  else if (normalized.includes("case")) className += " case";

  return <span className={className}>{formatLabel(value)}</span>;
}

function EventDetails({ event, onClose }) {
  if (!event) return null;

  const eventData = parseEventData(event.event_data);

  return (
    <div className="audit-modal-backdrop" onClick={onClose}>
      <section
        className="audit-detail-panel"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="audit-detail-header">
          <div>
            <span className="audit-eyebrow">EVENT DETAILS</span>
            <h2>Audit #{event.audit_id}</h2>
          </div>
          <button className="audit-icon-button" onClick={onClose}>
            <X size={19} />
          </button>
        </div>

        <div className="audit-detail-body">
          <div className="audit-detail-item">
            <span>Action</span>
            <strong>{formatLabel(event.action)}</strong>
          </div>

          <div className="audit-detail-item">
            <span>Timestamp</span>
            <strong>{formatDate(event.created_at)}</strong>
          </div>

          <div className="audit-detail-item">
            <span>Actor type</span>
            <strong>{formatLabel(event.actor_type)}</strong>
          </div>

          <div className="audit-detail-item">
            <span>Actor reference</span>
            <strong>{event.actor_reference || "—"}</strong>
          </div>

          <div className="audit-detail-item">
            <span>Entity type</span>
            <strong>{formatLabel(event.entity_type)}</strong>
          </div>

          <div className="audit-detail-item">
            <span>Entity reference</span>
            <strong>{event.entity_reference || "—"}</strong>
          </div>

          <div className="audit-detail-item">
            <span>Case ID</span>
            <strong>{event.case_id || "—"}</strong>
          </div>

          <div className="audit-event-data">
            <span>Event data</span>
            <pre>{JSON.stringify(eventData, null, 2)}</pre>
          </div>
        </div>
      </section>
    </div>
  );
}

export default function AuditHistory() {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [actorFilter, setActorFilter] = useState("ALL");
  const [entityFilter, setEntityFilter] = useState("ALL");
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadEvents = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/audit-logs", {
        params: {
          page,
          page_size: PAGE_SIZE,
        },
      });

      setEvents(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load audit history. Please check the API connection."
      );
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const filteredEvents = events.filter((event) => {
    const query = search.toLowerCase().trim();

    const searchable = [
      event.audit_id,
      event.action,
      event.actor_type,
      event.actor_reference,
      event.entity_type,
      event.entity_reference,
      event.case_id,
      event.event_data,
    ]
      .join(" ")
      .toLowerCase();

    const matchesSearch = !query || searchable.includes(query);
    const matchesActor =
      actorFilter === "ALL" || event.actor_type === actorFilter;
    const matchesEntity =
      entityFilter === "ALL" || event.entity_type === entityFilter;

    return matchesSearch && matchesActor && matchesEntity;
  });

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main className="audit-page">
      <header className="audit-page-header">
        <div>
          <span className="audit-eyebrow">SYSTEM TRANSPARENCY</span>
          <h1>Audit History</h1>
          <p>Track actions and maintain a traceable record of system activity.</p>
        </div>

        <button
          className="audit-refresh-button"
          onClick={loadEvents}
          disabled={loading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>

      <section className="audit-summary">
        <div className="audit-summary-icon">
          <ClipboardList size={23} />
        </div>
        <div>
          <span>Total recorded events</span>
          <strong>{total.toLocaleString("en-IN")}</strong>
          <small>Records available through the audit API</small>
        </div>
      </section>

      <section className="audit-content">
        <div className="audit-section-heading">
          <div>
            <h2>Activity log</h2>
            <p>Review recorded actions and their associated entities.</p>
          </div>
          <span className="audit-record-count">
            {total.toLocaleString("en-IN")} records
          </span>
        </div>

        <div className="audit-toolbar">
          <div className="audit-search">
            <Search size={17} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search this page..."
            />
          </div>

          <select
            value={actorFilter}
            onChange={(e) => setActorFilter(e.target.value)}
          >
            <option value="ALL">All actors</option>
            {[...new Set(events.map((e) => e.actor_type).filter(Boolean))]
              .sort()
              .map((actor) => (
                <option key={actor} value={actor}>
                  {formatLabel(actor)}
                </option>
              ))}
          </select>

          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
          >
            <option value="ALL">All entities</option>
            {[...new Set(events.map((e) => e.entity_type).filter(Boolean))]
              .sort()
              .map((entity) => (
                <option key={entity} value={entity}>
                  {formatLabel(entity)}
                </option>
              ))}
          </select>
        </div>

        <p className="audit-filter-note">
          Search and filters apply to the currently loaded page of records.
        </p>

        {error && (
          <div className="audit-error">
            {error}
            <button onClick={loadEvents}>Try again</button>
          </div>
        )}

        {loading ? (
          <div className="audit-empty">Loading audit records...</div>
        ) : !error && filteredEvents.length === 0 ? (
          <div className="audit-empty">No matching audit events found.</div>
        ) : !error ? (
          <>
            <div className="audit-table-wrap">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Action</th>
                    <th>Actor</th>
                    <th>Entity</th>
                    <th>Case reference</th>
                    <th>Timestamp</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.map((event) => (
                    <tr key={event.audit_id}>
                      <td>
                        <strong>#{event.audit_id}</strong>
                      </td>
                      <td>
                        <span className="audit-action">
                          {formatLabel(event.action)}
                        </span>
                      </td>
                      <td>
                        <EventBadge value={event.actor_type} />
                        <small className="audit-secondary">
                          {event.actor_reference || "—"}
                        </small>
                      </td>
                      <td>
                        <EventBadge value={event.entity_type} />
                        <small className="audit-secondary">
                          {event.entity_reference || "—"}
                        </small>
                      </td>
                      <td>{event.case_id || "—"}</td>
                      <td className="audit-date">
                        {formatDate(event.created_at)}
                      </td>
                      <td>
                        <button
                          className="audit-view-button"
                          onClick={() => setSelectedEvent(event)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="audit-pagination">
              <span>
                Page {page} of {totalPages} · Showing{" "}
                {filteredEvents.length} matching records on this page
              </span>

              <div>
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((current) => current - 1)}
                >
                  <ChevronLeft size={17} />
                  Previous
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Next
                  <ChevronRight size={17} />
                </button>
              </div>
            </div>
          </>
        ) : null}
      </section>

      <EventDetails
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />
    </main>
  );
}
