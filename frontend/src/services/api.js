
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api/v1",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ERR_NETWORK") {
      error.message =
        "Cannot connect to the API. Check that Docker backend is running and CORS is enabled.";
    } else if (error.response) {
      error.message = `API error ${error.response.status}: ${
        error.response.data?.detail || error.response.statusText
      }`;
    }
    return Promise.reject(error);
  }
);

// Dashboard
export const fetchDashboard = async () => {
  const { data } = await api.get("/dashboard/summary");
  return data;
};

// Cases
export const fetchCases = async (page = 1, pageSize = 8) => {
  const { data } = await api.get("/cases", {
    params: { page, page_size: pageSize },
  });
  return data;
};

export const fetchCase = async (caseId) => {
  const { data } = await api.get(`/cases/${caseId}`);
  return data;
};

export const fetchCaseTimeline = async (caseId) => {
  const { data } = await api.get(`/cases/${caseId}/timeline`);
  return data;
};

// Appeals

export const fetchAppeals = async () => {
  const { data } = await api.get("/appeals", {
    params: {
      page: 1,
      page_size: 100,
    },
  });

  return data;
};


// Decisions
export const fetchDecisions = async (
  page = 1,
  pageSize = 20,
  filters = {}
) => {
  const params = {
    page,
    page_size: pageSize,
  };

  if (filters.case_id) {
    params.case_id = filters.case_id;
  }

  if (filters.reviewer_id) {
    params.reviewer_id = filters.reviewer_id;
  }

  if (filters.decision_type) {
    params.decision_type = filters.decision_type;
  }

  if (filters.decision_stage) {
    params.decision_stage = filters.decision_stage;
  }

  const { data } = await api.get("/decisions", { params });
  return data;
};

export const fetchDecision = async (decisionId) => {
  const { data } = await api.get(`/decisions/${decisionId}`);
  return data;
};

// Audit logs
export const fetchAuditLogs = async () => {
  const { data } = await api.get("/audit-logs");
  return data;
};

// Reviewers
export async function fetchReviewers() {
  const response = await api.get("/reviewers", {
    params: {
      page: 1,
      page_size: 100,
      active_only: false,
    },
  });

  return response.data;
}

// Reviewer assignments
export async function fetchReviewerAssignments() {
  const first = await api.get("/reviewer-assignments", {
    params: { page: 1, page_size: 100 },
  });

  const data = first.data;
  const total = data.total ?? data.assignments?.length ?? 0;
  const pages = Math.ceil(total / 100);

  const remaining = await Promise.all(
    Array.from({ length: Math.max(0, pages - 1) }, (_, index) =>
      api.get("/reviewer-assignments", {
        params: { page: index + 2, page_size: 100 },
      })
    )
  );

  return {
    ...data,
    assignments: [
      ...(data.assignments ?? []),
      ...remaining.flatMap((response) =>
        response.data.assignments ?? []
      ),
    ],
  };
}

// Similarity reports
export async function fetchSimilarityReports(
  page = 1,
  pageSize = 20,
  filters = {}
) {
  const response = await api.get("/similarity-reports", {
    params: {
      page,
      page_size: pageSize,
      ...(filters.review_action
        ? { review_action: filters.review_action }
        : {}),
      ...(filters.report_category
        ? { report_category: filters.report_category }
        : {}),
    },
  });

  return response.data;
}

export async function fetchSimilarityReport(reportId) {
  const response = await api.get(
    `/similarity-reports/${encodeURIComponent(reportId)}`
  );

  return response.data;
}

export default api;
