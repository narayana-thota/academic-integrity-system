
-- =========================================================
-- YOTTAFLEX: ACADEMIC INTEGRITY CASE MANAGEMENT SYSTEM
-- Database: academic_integrity
-- Engine: MySQL 8.4 / InnoDB
-- =========================================================

USE academic_integrity;

-- =========================================================
-- 1. MASTER TABLES
-- =========================================================

CREATE TABLE IF NOT EXISTS learners (
    learner_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    learner_code VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    assessment_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    assessment_type VARCHAR(30) NOT NULL,
    description TEXT,
    due_date DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_assessment_type CHECK (
        assessment_type IN (
            'ASSIGNMENT', 'EXAM', 'PROJECT', 'QUIZ'
        )
    )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reviewers (
    reviewer_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    reviewer_code VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL,
    department VARCHAR(100) NOT NULL,
    max_active_cases INT UNSIGNED NOT NULL DEFAULT 5,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_reviewer_role CHECK (
        role IN ('INSTRUCTOR', 'ADMIN', 'REVIEWER')
    ),

    CONSTRAINT chk_reviewer_capacity CHECK (
        max_active_cases > 0
    )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS integrity_rules (
    rule_id VARCHAR(30) PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    description TEXT,
    minimum_score DECIMAL(5,2) NOT NULL,
    maximum_score DECIMAL(5,2) NOT NULL,
    action VARCHAR(30) NOT NULL,
    rule_version INT UNSIGNED NOT NULL DEFAULT 1,
    effective_from DATETIME NOT NULL,
    effective_to DATETIME,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_rule_minimum CHECK (
        minimum_score BETWEEN 0 AND 100
    ),

    CONSTRAINT chk_rule_maximum CHECK (
        maximum_score BETWEEN 0 AND 100
    ),

    CONSTRAINT chk_rule_range CHECK (
        maximum_score >= minimum_score
    ),

    CONSTRAINT chk_rule_dates CHECK (
        effective_to IS NULL OR effective_to > effective_from
    ),

    CONSTRAINT chk_rule_action CHECK (
        action IN ('NO_FLAG', 'MONITOR', 'REVIEW')
    ),

    CONSTRAINT uq_rule_version UNIQUE (rule_name, rule_version)
) ENGINE=InnoDB;

-- =========================================================
-- 2. SUBMISSIONS AND SIMILARITY REPORTS
-- =========================================================

CREATE TABLE IF NOT EXISTS submissions (
    submission_id VARCHAR(40) PRIMARY KEY,
    learner_id BIGINT UNSIGNED NOT NULL,
    assessment_id BIGINT UNSIGNED NOT NULL,
    submitted_at DATETIME NOT NULL,
    content_reference VARCHAR(500) NOT NULL,
    content_hash CHAR(64),
    attempt_number INT UNSIGNED NOT NULL DEFAULT 1,
    status VARCHAR(30) NOT NULL DEFAULT 'SUBMITTED',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_submission_learner
        FOREIGN KEY (learner_id)
        REFERENCES learners(learner_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_submission_assessment
        FOREIGN KEY (assessment_id)
        REFERENCES assessments(assessment_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_submission_attempt
        UNIQUE (learner_id, assessment_id, attempt_number),

    CONSTRAINT chk_submission_attempt
        CHECK (attempt_number > 0),

    CONSTRAINT chk_submission_status CHECK (
        status IN (
            'SUBMITTED', 'PROCESSING', 'ANALYZED', 'REJECTED'
        )
    ),

    INDEX idx_submission_learner (learner_id),
    INDEX idx_submission_assessment (assessment_id),
    INDEX idx_submission_date (submitted_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS similarity_reports (
    report_id VARCHAR(100) PRIMARY KEY,
    submission_id VARCHAR(40) NOT NULL,
    evaluated_rule_id VARCHAR(30),
    similarity_score DECIMAL(5,2) NOT NULL,
    matched_source_count INT UNSIGNED NOT NULL DEFAULT 0,
    report_category VARCHAR(30) NOT NULL,
    review_action VARCHAR(30) NOT NULL,
    generated_at DATETIME NOT NULL,
    generator_version VARCHAR(30) NOT NULL,

    CONSTRAINT fk_report_submission
        FOREIGN KEY (submission_id)
        REFERENCES submissions(submission_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_report_rule
        FOREIGN KEY (evaluated_rule_id)
        REFERENCES integrity_rules(rule_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_similarity_score CHECK (
        similarity_score BETWEEN 0 AND 100
    ),

    CONSTRAINT chk_report_category CHECK (
        report_category IN (
            'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
        )
    ),

    CONSTRAINT chk_review_action CHECK (
        review_action IN (
            'NO_FLAG', 'MONITOR', 'REVIEW'
        )
    ),

    INDEX idx_report_submission (submission_id),
    INDEX idx_report_score (similarity_score),
    INDEX idx_report_action (review_action)
) ENGINE=InnoDB;

-- =========================================================
-- 3. INVESTIGATION CASES
-- =========================================================

CREATE TABLE IF NOT EXISTS cases (
    case_id VARCHAR(30) PRIMARY KEY,
    submission_id VARCHAR(40) NOT NULL,
    report_id VARCHAR(100) NOT NULL UNIQUE,
    rule_id VARCHAR(30) NOT NULL,
    case_status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_at DATETIME,
    closed_at DATETIME,
    closure_reason TEXT,

    CONSTRAINT fk_case_submission
        FOREIGN KEY (submission_id)
        REFERENCES submissions(submission_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_case_report
        FOREIGN KEY (report_id)
        REFERENCES similarity_reports(report_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_case_rule
        FOREIGN KEY (rule_id)
        REFERENCES integrity_rules(rule_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_case_status CHECK (
        case_status IN (
            'OPEN', 'ASSIGNED', 'UNDER_REVIEW',
            'DECIDED', 'APPEALED', 'APPEAL_REVIEW',
            'CLOSED'
        )
    ),

    CONSTRAINT chk_case_priority CHECK (
        priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),

    CONSTRAINT chk_case_dates CHECK (
        (due_at IS NULL OR due_at >= created_at)
        AND
        (closed_at IS NULL OR closed_at >= created_at)
    ),

    CONSTRAINT chk_case_closure CHECK (
        case_status <> 'CLOSED'
        OR (
            closed_at IS NOT NULL
            AND closure_reason IS NOT NULL
        )
    ),

    INDEX idx_case_status (case_status),
    INDEX idx_case_priority (priority),
    INDEX idx_case_submission (submission_id)
) ENGINE=InnoDB;

-- =========================================================
-- 4. EVIDENCE MANAGEMENT
-- =========================================================

CREATE TABLE IF NOT EXISTS evidence_items (
    evidence_id VARCHAR(100) PRIMARY KEY,
    evidence_type VARCHAR(30) NOT NULL,
    evidence_reference VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    content_hash CHAR(64),
    version INT UNSIGNED NOT NULL DEFAULT 1,
    added_by VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_evidence_type CHECK (
        evidence_type IN (
            'CODE_MATCH', 'TEXT_MATCH',
            'DOCUMENT', 'STATEMENT', 'OTHER'
        )
    ),

    CONSTRAINT chk_evidence_version CHECK (
        version > 0
    )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS case_evidence (
    case_evidence_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    case_id VARCHAR(30) NOT NULL,
    evidence_id VARCHAR(100) NOT NULL,
    linked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_case_evidence_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_case_evidence_item
        FOREIGN KEY (evidence_id)
        REFERENCES evidence_items(evidence_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_case_evidence
        UNIQUE (case_id, evidence_id)
) ENGINE=InnoDB;

-- =========================================================
-- 5. REVIEWER CONFLICTS AND ASSIGNMENTS
-- =========================================================

CREATE TABLE IF NOT EXISTS reviewer_conflicts (
    conflict_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    reviewer_id BIGINT UNSIGNED NOT NULL,
    learner_id BIGINT UNSIGNED,
    assessment_id BIGINT UNSIGNED,
    conflict_type VARCHAR(40) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_conflict_reviewer
        FOREIGN KEY (reviewer_id)
        REFERENCES reviewers(reviewer_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_conflict_learner
        FOREIGN KEY (learner_id)
        REFERENCES learners(learner_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_conflict_assessment
        FOREIGN KEY (assessment_id)
        REFERENCES assessments(assessment_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_conflict_target CHECK (
        learner_id IS NOT NULL OR assessment_id IS NOT NULL
    ),

    INDEX idx_conflict_reviewer (reviewer_id, is_active)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reviewer_assignments (
    assignment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    case_id VARCHAR(30) NOT NULL,
    reviewer_id BIGINT UNSIGNED NOT NULL,
    assignment_status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    assigned_by VARCHAR(100) NOT NULL,
    end_reason TEXT,

    CONSTRAINT fk_assignment_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_assignment_reviewer
        FOREIGN KEY (reviewer_id)
        REFERENCES reviewers(reviewer_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_assignment_status CHECK (
        assignment_status IN (
            'ACTIVE', 'COMPLETED', 'REVOKED'
        )
    ),

    CONSTRAINT chk_assignment_dates CHECK (
        ended_at IS NULL OR ended_at >= assigned_at
    ),

    INDEX idx_assignment_case (case_id),
    INDEX idx_assignment_reviewer (reviewer_id),
    INDEX idx_assignment_status (assignment_status)
) ENGINE=InnoDB;

-- =========================================================
-- 6. REPORT MATCHES
-- =========================================================

CREATE TABLE IF NOT EXISTS report_matches (
    match_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    report_id VARCHAR(100) NOT NULL,
    match_sequence INT UNSIGNED NOT NULL,
    source_reference VARCHAR(500) NOT NULL,
    match_percentage DECIMAL(5,2) NOT NULL,
    match_type VARCHAR(30) NOT NULL,
    description TEXT,

    CONSTRAINT fk_match_report
        FOREIGN KEY (report_id)
        REFERENCES similarity_reports(report_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_match_percentage CHECK (
        match_percentage BETWEEN 0 AND 100
    ),

    CONSTRAINT uq_report_match_sequence
        UNIQUE (report_id, match_sequence)
) ENGINE=InnoDB;

-- =========================================================
-- 7. DECISION MANAGEMENT
-- =========================================================

CREATE TABLE IF NOT EXISTS decisions (
    decision_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    case_id VARCHAR(30) NOT NULL,
    reviewer_id BIGINT UNSIGNED NOT NULL,
    decision_type VARCHAR(40) NOT NULL,
    decision_stage VARCHAR(20) NOT NULL DEFAULT 'INITIAL',
    rationale TEXT NOT NULL,
    decided_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    supersedes_decision_id BIGINT UNSIGNED,

    CONSTRAINT fk_decision_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_decision_reviewer
        FOREIGN KEY (reviewer_id)
        REFERENCES reviewers(reviewer_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_decision_supersedes
        FOREIGN KEY (supersedes_decision_id)
        REFERENCES decisions(decision_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_decision_type CHECK (
        decision_type IN (
            'NO_VIOLATION',
            'ACADEMIC_MISCONDUCT',
            'INSUFFICIENT_EVIDENCE',
            'REQUEST_MORE_EVIDENCE',
            'UPHELD', 'OVERTURNED', 'MODIFIED'
        )
    ),

    CONSTRAINT chk_decision_stage CHECK (
        decision_stage IN ('INITIAL', 'REASSESSMENT')
    ),

    INDEX idx_decision_case (case_id)
) ENGINE=InnoDB;

-- =========================================================
-- 8. APPEALS AND INDEPENDENT REVIEWS
-- =========================================================

CREATE TABLE IF NOT EXISTS appeals (
    appeal_id VARCHAR(100) PRIMARY KEY,
    case_id VARCHAR(30) NOT NULL,
    original_decision_id BIGINT UNSIGNED NOT NULL,
    submitted_by_learner_id BIGINT UNSIGNED NOT NULL,
    appeal_reason TEXT NOT NULL,
    appeal_status VARCHAR(30) NOT NULL DEFAULT 'SUBMITTED',
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_at DATETIME,
    outcome VARCHAR(30),
    resolved_at DATETIME,

    CONSTRAINT fk_appeal_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_appeal_decision
        FOREIGN KEY (original_decision_id)
        REFERENCES decisions(decision_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_appeal_learner
        FOREIGN KEY (submitted_by_learner_id)
        REFERENCES learners(learner_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_appeal_status CHECK (
        appeal_status IN (
            'SUBMITTED', 'ELIGIBILITY_REVIEW',
            'ASSIGNED', 'UNDER_REVIEW',
            'RESOLVED', 'REJECTED', 'WITHDRAWN'
        )
    ),

    CONSTRAINT chk_appeal_outcome CHECK (
        outcome IS NULL OR
        outcome IN ('UPHELD', 'OVERTURNED', 'MODIFIED')
    ),

    CONSTRAINT chk_appeal_dates CHECK (
        resolved_at IS NULL OR resolved_at >= submitted_at
    ),

    INDEX idx_appeal_case (case_id),
    INDEX idx_appeal_status (appeal_status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS appeal_reviews (
    appeal_review_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    appeal_id VARCHAR(100) NOT NULL,
    reviewer_id BIGINT UNSIGNED NOT NULL,
    outcome VARCHAR(30) NOT NULL,
    rationale TEXT NOT NULL,
    reviewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_appeal_review_appeal
        FOREIGN KEY (appeal_id)
        REFERENCES appeals(appeal_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_appeal_review_reviewer
        FOREIGN KEY (reviewer_id)
        REFERENCES reviewers(reviewer_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_appeal_review_outcome CHECK (
        outcome IN ('UPHELD', 'OVERTURNED', 'MODIFIED')
    ),

    INDEX idx_appeal_review_appeal (appeal_id)
) ENGINE=InnoDB;

-- =========================================================
-- 9. CASE TIMELINE AND AUDIT HISTORY
-- =========================================================

CREATE TABLE IF NOT EXISTS case_events (
    event_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    case_id VARCHAR(30) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT NOT NULL,
    actor_reference VARCHAR(100) NOT NULL,
    event_data JSON,
    occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_event_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
        ON DELETE RESTRICT,

    INDEX idx_event_case_date (case_id, occurred_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    case_id VARCHAR(30),
    actor_type VARCHAR(30) NOT NULL,
    actor_reference VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_reference VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    event_data JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_case
        FOREIGN KEY (case_id)
        REFERENCES cases(case_id)
        ON DELETE RESTRICT,

    INDEX idx_audit_case (case_id),
    INDEX idx_audit_entity (entity_type, entity_reference),
    INDEX idx_audit_date (created_at)
) ENGINE=InnoDB;

-- =========================================================
-- SCHEMA CREATION COMPLETE
-- =========================================================
