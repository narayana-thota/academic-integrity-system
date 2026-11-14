
import { useState } from "react";
import { ChevronDown, ChevronUp, Clock3, UserRound } from "lucide-react";

function formatDate(value) {
  if (!value) return "Date unavailable";

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
}

function formatLabel(value) {
  return String(value || "CASE ACTIVITY")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function parseEventData(value) {
  if (!value) return null;

  if (typeof value === "object") return value;

  try {
    return JSON.parse(value);
  } catch {
    return { details: value };
  }
}

function getEventStyle(type) {
  const value = String(type || "").toUpperCase();

  if (value.includes("CASE_CREATED")) return "created";
  if (value.includes("EVIDENCE")) return "evidence";
  if (value.includes("REVIEWER")) return "reviewer";
  if (value.includes("DECISION")) return "decision";
  if (value.includes("APPEAL")) return "appeal";
  if (value.includes("CLOSED")) return "closed";
  if (value.includes("STATUS")) return "status";

  return "default";
}

function TimelineEvent({ event, isLast }) {
  const [expanded, setExpanded] = useState(false);

  const eventData = parseEventData(event.event_data);
  const hasData = eventData && Object.keys(eventData).length > 0;

  return (
    <div className={`timeline-event ${isLast ? "last-event" : ""}`}>
      <div className="timeline-track">
        <div className={`timeline-marker ${getEventStyle(event.event_type)}`} />
        {!isLast && <div className="timeline-line" />}
      </div>

      <div className="timeline-content">
        <div className="timeline-event-heading">
          <div>
            <span className={`timeline-type ${getEventStyle(event.event_type)}`}>
              {formatLabel(event.event_type)}
            </span>

            <h3>{event.event_description || "Case activity recorded"}</h3>
          </div>

          <time>
            <Clock3 size={13} />
            {formatDate(event.occurred_at)}
          </time>
        </div>

        <div className="timeline-event-footer">
          <span className="timeline-actor">
            <UserRound size={13} />
            {event.actor_reference || "Unknown actor"}
          </span>

          <span className="timeline-event-id">
            Event #{event.event_id}
          </span>
        </div>

        {hasData && (
          <div className="timeline-extra">
            <button
              type="button"
              className="timeline-expand"
              onClick={() => setExpanded((current) => !current)}
            >
              {expanded ? "Hide event details" : "View event details"}
              {expanded ? (
                <ChevronUp size={15} />
              ) : (
                <ChevronDown size={15} />
              )}
            </button>

            {expanded && (
              <pre className="timeline-event-data">
                {JSON.stringify(eventData, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function CaseTimeline({ events = [] }) {
  const chronologicalEvents = [...events].sort(
    (a, b) =>
      new Date(a.occurred_at || 0).getTime() -
      new Date(b.occurred_at || 0).getTime()
  );

  return (
    <section className="detail-card">
      <div className="detail-card-heading">
        <div>
          <p className="eyebrow">CASE ACTIVITY</p>
          <h2>Investigation timeline</h2>
          <p className="timeline-subtitle">
            A chronological record of case events and decisions.
          </p>
        </div>

        <span className="count-label">
          {chronologicalEvents.length} events
        </span>
      </div>

      {chronologicalEvents.length === 0 ? (
        <div className="empty-detail">
          No timeline events are available for this case.
        </div>
      ) : (
        <div className="timeline">
          {chronologicalEvents.map((event, index) => (
            <TimelineEvent
              key={event.event_id ?? index}
              event={event}
              isLast={index === chronologicalEvents.length - 1}
            />
          ))}
        </div>
      )}
    </section>
  );
}
