# Academic Integrity Case Management System

## Database Data Dictionary

- Database: `academic_integrity`
- Engine: MySQL 8.4 / InnoDB
- Tables documented: 17
- Source: Live MySQL schema inspection

## Table overview

| Table | Purpose |
|---|---|
| `appeal_reviews` | Independent reviewer assessments of appeals. |
| `appeals` | Learner appeals against original case decisions. |
| `assessments` | Academic assessments to which submissions belong. |
| `audit_logs` | Audit records tracking actions and affected entities. |
| `case_events` | Chronological case timeline events. |
| `case_evidence` | Bridge table linking cases to evidence items. |
| `cases` | Formal academic integrity investigations. |
| `decisions` | Initial and reassessment decisions with reviewer rationale. |
| `evidence_items` | Evidence records collected during investigations. |
| `integrity_rules` | Versioned similarity thresholds and their corresponding review actions. |
| `learners` | Master records for learners who submit academic work. |
| `report_matches` | Individual matched sources within similarity reports. |
| `reviewer_assignments` | Reviewer assignment history for investigation cases. |
| `reviewer_conflicts` | Declared reviewer conflicts involving learners or assessments. |
| `reviewers` | Instructors and administrators who review integrity cases. |
| `similarity_reports` | Similarity analysis results generated for submissions. |
| `submissions` | Learner submissions associated with assessments. |

## appeal_reviews

Independent reviewer assessments of appeals.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `appeal_review_id` | `BIGINT` | No | `` | PK |
| `appeal_id` | `VARCHAR(100)` | No | `` | FK → appeals.appeal_id |
| `reviewer_id` | `BIGINT` | No | `` | FK → reviewers.reviewer_id |
| `outcome` | `VARCHAR(30)` | No | `` |  |
| `rationale` | `TEXT` | No | `` |  |
| `reviewed_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- `appeal_id` → `appeals.appeal_id`
- `reviewer_id` → `reviewers.reviewer_id`

### Unique constraints

- No additional unique constraints.

### Check constraints

- `chk_appeal_review_outcome`: `(`outcome` in (_latin1'UPHELD',_latin1'OVERTURNED',_latin1'MODIFIED'))`

### Indexes

- `fk_appeal_review_reviewer` (NON-UNIQUE): `reviewer_id`
- `idx_appeal_review_appeal` (NON-UNIQUE): `appeal_id`

## appeals

Learner appeals against original case decisions.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `appeal_id` | `VARCHAR(100)` | No | `` | PK |
| `case_id` | `VARCHAR(30)` | No | `` | FK → cases.case_id |
| `original_decision_id` | `BIGINT` | No | `` | FK → decisions.decision_id |
| `submitted_by_learner_id` | `BIGINT` | No | `` | FK → learners.learner_id |
| `appeal_reason` | `TEXT` | No | `` |  |
| `appeal_status` | `VARCHAR(30)` | No | `'SUBMITTED'` |  |
| `submitted_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |
| `due_at` | `DATETIME` | Yes | `` |  |
| `outcome` | `VARCHAR(30)` | Yes | `` |  |
| `resolved_at` | `DATETIME` | Yes | `` |  |

### Foreign-key relationships

- `case_id` → `cases.case_id`
- `original_decision_id` → `decisions.decision_id`
- `submitted_by_learner_id` → `learners.learner_id`

### Unique constraints

- No additional unique constraints.

### Check constraints

- `chk_appeal_dates`: `((`resolved_at` is null) or (`resolved_at` >= `submitted_at`))`
- `chk_appeal_outcome`: `((`outcome` is null) or (`outcome` in (_latin1'UPHELD',_latin1'OVERTURNED',_latin1'MODIFIED')))`
- `chk_appeal_status`: `(`appeal_status` in (_latin1'SUBMITTED',_latin1'ELIGIBILITY_REVIEW',_latin1'ASSIGNED',_latin1'UNDER_REVIEW',_latin1'RESOLVED',_latin1'REJECTED',_latin1'WITHDRAWN'))`

### Indexes

- `fk_appeal_decision` (NON-UNIQUE): `original_decision_id`
- `fk_appeal_learner` (NON-UNIQUE): `submitted_by_learner_id`
- `idx_appeal_case` (NON-UNIQUE): `case_id`
- `idx_appeal_status` (NON-UNIQUE): `appeal_status`

## assessments

Academic assessments to which submissions belong.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `assessment_id` | `BIGINT` | No | `` | PK |
| `assessment_code` | `VARCHAR(30)` | No | `` | UNIQUE |
| `title` | `VARCHAR(200)` | No | `` |  |
| `assessment_type` | `VARCHAR(30)` | No | `` |  |
| `description` | `TEXT` | Yes | `` |  |
| `due_date` | `DATETIME` | No | `` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- No foreign keys.

### Unique constraints

- `assessment_code`: `assessment_code`

### Check constraints

- `chk_assessment_type`: `(`assessment_type` in (_latin1'ASSIGNMENT',_latin1'EXAM',_latin1'PROJECT',_latin1'QUIZ'))`

### Indexes

- `assessment_code` (UNIQUE): `assessment_code`

## audit_logs

Audit records tracking actions and affected entities.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `audit_id` | `BIGINT` | No | `` | PK |
| `case_id` | `VARCHAR(30)` | Yes | `` | FK → cases.case_id |
| `actor_type` | `VARCHAR(30)` | No | `` |  |
| `actor_reference` | `VARCHAR(100)` | No | `` |  |
| `entity_type` | `VARCHAR(50)` | No | `` |  |
| `entity_reference` | `VARCHAR(100)` | No | `` |  |
| `action` | `VARCHAR(50)` | No | `` |  |
| `event_data` | `JSON` | Yes | `` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- `case_id` → `cases.case_id`

### Unique constraints

- No additional unique constraints.

### Check constraints

- No check constraints reported by the database.

### Indexes

- `idx_audit_case` (NON-UNIQUE): `case_id`
- `idx_audit_date` (NON-UNIQUE): `created_at`
- `idx_audit_entity` (NON-UNIQUE): `entity_type, entity_reference`

## case_events

Chronological case timeline events.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `event_id` | `BIGINT` | No | `` | PK |
| `case_id` | `VARCHAR(30)` | No | `` | FK → cases.case_id |
| `event_type` | `VARCHAR(50)` | No | `` |  |
| `event_description` | `TEXT` | No | `` |  |
| `actor_reference` | `VARCHAR(100)` | No | `` |  |
| `event_data` | `JSON` | Yes | `` |  |
| `occurred_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- `case_id` → `cases.case_id`

### Unique constraints

- No additional unique constraints.

### Check constraints

- No check constraints reported by the database.

### Indexes

- `idx_event_case_date` (NON-UNIQUE): `case_id, occurred_at`

## case_evidence

Bridge table linking cases to evidence items.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `case_evidence_id` | `BIGINT` | No | `` | PK |
| `case_id` | `VARCHAR(30)` | No | `` | FK → cases.case_id, UNIQUE |
| `evidence_id` | `VARCHAR(100)` | No | `` | FK → evidence_items.evidence_id, UNIQUE |
| `linked_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- `case_id` → `cases.case_id`
- `evidence_id` → `evidence_items.evidence_id`

### Unique constraints

- `uq_case_evidence`: `case_id, evidence_id`

### Check constraints

- No check constraints reported by the database.

### Indexes

- `fk_case_evidence_item` (NON-UNIQUE): `evidence_id`
- `uq_case_evidence` (UNIQUE): `case_id, evidence_id`

## cases

Formal academic integrity investigations.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `case_id` | `VARCHAR(30)` | No | `` | PK |
| `submission_id` | `VARCHAR(40)` | No | `` | FK → submissions.submission_id |
| `report_id` | `VARCHAR(100)` | No | `` | FK → similarity_reports.report_id, UNIQUE |
| `rule_id` | `VARCHAR(30)` | No | `` | FK → integrity_rules.rule_id |
| `case_status` | `VARCHAR(30)` | No | `'OPEN'` |  |
| `priority` | `VARCHAR(20)` | No | `'MEDIUM'` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |
| `due_at` | `DATETIME` | Yes | `` |  |
| `closed_at` | `DATETIME` | Yes | `` |  |
| `closure_reason` | `TEXT` | Yes | `` |  |

### Foreign-key relationships

- `report_id` → `similarity_reports.report_id`
- `rule_id` → `integrity_rules.rule_id`
- `submission_id` → `submissions.submission_id`

### Unique constraints

- `report_id`: `report_id`

### Check constraints

- `chk_case_closure`: `((`case_status` <> _latin1'CLOSED') or ((`closed_at` is not null) and (`closure_reason` is not null)))`
- `chk_case_dates`: `(((`due_at` is null) or (`due_at` >= `created_at`)) and ((`closed_at` is null) or (`closed_at` >= `created_at`)))`
- `chk_case_priority`: `(`priority` in (_latin1'LOW',_latin1'MEDIUM',_latin1'HIGH',_latin1'CRITICAL'))`
- `chk_case_status`: `(`case_status` in (_latin1'OPEN',_latin1'ASSIGNED',_latin1'UNDER_REVIEW',_latin1'DECIDED',_latin1'APPEALED',_latin1'APPEAL_REVIEW',_latin1'CLOSED'))`

### Indexes

- `fk_case_rule` (NON-UNIQUE): `rule_id`
- `idx_case_priority` (NON-UNIQUE): `priority`
- `idx_case_status` (NON-UNIQUE): `case_status`
- `idx_case_submission` (NON-UNIQUE): `submission_id`
- `report_id` (UNIQUE): `report_id`

## decisions

Initial and reassessment decisions with reviewer rationale.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `decision_id` | `BIGINT` | No | `` | PK |
| `case_id` | `VARCHAR(30)` | No | `` | FK → cases.case_id |
| `reviewer_id` | `BIGINT` | No | `` | FK → reviewers.reviewer_id |
| `decision_type` | `VARCHAR(40)` | No | `` |  |
| `decision_stage` | `VARCHAR(20)` | No | `'INITIAL'` |  |
| `rationale` | `TEXT` | No | `` |  |
| `decided_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |
| `supersedes_decision_id` | `BIGINT` | Yes | `` | FK → decisions.decision_id |

### Foreign-key relationships

- `case_id` → `cases.case_id`
- `reviewer_id` → `reviewers.reviewer_id`
- `supersedes_decision_id` → `decisions.decision_id`

### Unique constraints

- No additional unique constraints.

### Check constraints

- `chk_decision_stage`: `(`decision_stage` in (_latin1'INITIAL',_latin1'REASSESSMENT'))`
- `chk_decision_type`: `(`decision_type` in (_latin1'NO_VIOLATION',_latin1'ACADEMIC_MISCONDUCT',_latin1'INSUFFICIENT_EVIDENCE',_latin1'REQUEST_MORE_EVIDENCE',_latin1'UPHELD',_latin1'OVERTURNED',_latin1'MODIFIED'))`

### Indexes

- `fk_decision_reviewer` (NON-UNIQUE): `reviewer_id`
- `fk_decision_supersedes` (NON-UNIQUE): `supersedes_decision_id`
- `idx_decision_case` (NON-UNIQUE): `case_id`

## evidence_items

Evidence records collected during investigations.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `evidence_id` | `VARCHAR(100)` | No | `` | PK |
| `evidence_type` | `VARCHAR(30)` | No | `` |  |
| `evidence_reference` | `VARCHAR(500)` | No | `` |  |
| `description` | `TEXT` | No | `` |  |
| `content_hash` | `CHAR(64)` | Yes | `` |  |
| `version` | `INTEGER` | No | `'1'` |  |
| `added_by` | `VARCHAR(100)` | No | `` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- No foreign keys.

### Unique constraints

- No additional unique constraints.

### Check constraints

- `chk_evidence_type`: `(`evidence_type` in (_latin1'CODE_MATCH',_latin1'TEXT_MATCH',_latin1'DOCUMENT',_latin1'STATEMENT',_latin1'OTHER'))`
- `chk_evidence_version`: `(`version` > 0)`

### Indexes

- No additional indexes.

## integrity_rules

Versioned similarity thresholds and their corresponding review actions.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `rule_id` | `VARCHAR(30)` | No | `` | PK |
| `rule_name` | `VARCHAR(100)` | No | `` | UNIQUE |
| `description` | `TEXT` | Yes | `` |  |
| `minimum_score` | `DECIMAL(5, 2)` | No | `` |  |
| `maximum_score` | `DECIMAL(5, 2)` | No | `` |  |
| `action` | `VARCHAR(30)` | No | `` |  |
| `rule_version` | `INTEGER` | No | `'1'` | UNIQUE |
| `effective_from` | `DATETIME` | No | `` |  |
| `effective_to` | `DATETIME` | Yes | `` |  |
| `is_active` | `TINYINT` | No | `'1'` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- No foreign keys.

### Unique constraints

- `uq_rule_version`: `rule_name, rule_version`

### Check constraints

- `chk_rule_action`: `(`action` in (_latin1'NO_FLAG',_latin1'MONITOR',_latin1'REVIEW'))`
- `chk_rule_dates`: `((`effective_to` is null) or (`effective_to` > `effective_from`))`
- `chk_rule_maximum`: `(`maximum_score` between 0 and 100)`
- `chk_rule_minimum`: `(`minimum_score` between 0 and 100)`
- `chk_rule_range`: `(`maximum_score` >= `minimum_score`)`

### Indexes

- `uq_rule_version` (UNIQUE): `rule_name, rule_version`

## learners

Master records for learners who submit academic work.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `learner_id` | `BIGINT` | No | `` | PK |
| `learner_code` | `VARCHAR(30)` | No | `` | UNIQUE |
| `full_name` | `VARCHAR(120)` | No | `` |  |
| `email` | `VARCHAR(150)` | No | `` | UNIQUE |
| `department` | `VARCHAR(100)` | No | `` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |
| `updated_at` | `DATETIME` | No | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- No foreign keys.

### Unique constraints

- `email`: `email`
- `learner_code`: `learner_code`

### Check constraints

- No check constraints reported by the database.

### Indexes

- `email` (UNIQUE): `email`
- `learner_code` (UNIQUE): `learner_code`

## report_matches

Individual matched sources within similarity reports.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `match_id` | `BIGINT` | No | `` | PK |
| `report_id` | `VARCHAR(100)` | No | `` | FK → similarity_reports.report_id, UNIQUE |
| `match_sequence` | `INTEGER` | No | `` | UNIQUE |
| `source_reference` | `VARCHAR(500)` | No | `` |  |
| `match_percentage` | `DECIMAL(5, 2)` | No | `` |  |
| `match_type` | `VARCHAR(30)` | No | `` |  |
| `description` | `TEXT` | Yes | `` |  |

### Foreign-key relationships

- `report_id` → `similarity_reports.report_id`

### Unique constraints

- `uq_report_match_sequence`: `report_id, match_sequence`

### Check constraints

- `chk_match_percentage`: `(`match_percentage` between 0 and 100)`

### Indexes

- `uq_report_match_sequence` (UNIQUE): `report_id, match_sequence`

## reviewer_assignments

Reviewer assignment history for investigation cases.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `assignment_id` | `BIGINT` | No | `` | PK |
| `case_id` | `VARCHAR(30)` | No | `` | FK → cases.case_id |
| `reviewer_id` | `BIGINT` | No | `` | FK → reviewers.reviewer_id |
| `assignment_status` | `VARCHAR(30)` | No | `'ACTIVE'` |  |
| `assigned_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |
| `ended_at` | `DATETIME` | Yes | `` |  |
| `assigned_by` | `VARCHAR(100)` | No | `` |  |
| `end_reason` | `TEXT` | Yes | `` |  |

### Foreign-key relationships

- `case_id` → `cases.case_id`
- `reviewer_id` → `reviewers.reviewer_id`

### Unique constraints

- No additional unique constraints.

### Check constraints

- `chk_assignment_dates`: `((`ended_at` is null) or (`ended_at` >= `assigned_at`))`
- `chk_assignment_status`: `(`assignment_status` in (_latin1'ACTIVE',_latin1'COMPLETED',_latin1'REVOKED'))`

### Indexes

- `idx_assignment_case` (NON-UNIQUE): `case_id`
- `idx_assignment_reviewer` (NON-UNIQUE): `reviewer_id`
- `idx_assignment_status` (NON-UNIQUE): `assignment_status`

## reviewer_conflicts

Declared reviewer conflicts involving learners or assessments.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `conflict_id` | `BIGINT` | No | `` | PK |
| `reviewer_id` | `BIGINT` | No | `` | FK → reviewers.reviewer_id |
| `learner_id` | `BIGINT` | Yes | `` | FK → learners.learner_id |
| `assessment_id` | `BIGINT` | Yes | `` | FK → assessments.assessment_id |
| `conflict_type` | `VARCHAR(40)` | No | `` |  |
| `description` | `TEXT` | Yes | `` |  |
| `is_active` | `TINYINT` | No | `'1'` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- `assessment_id` → `assessments.assessment_id`
- `learner_id` → `learners.learner_id`
- `reviewer_id` → `reviewers.reviewer_id`

### Unique constraints

- No additional unique constraints.

### Check constraints

- `chk_conflict_target`: `((`learner_id` is not null) or (`assessment_id` is not null))`

### Indexes

- `fk_conflict_assessment` (NON-UNIQUE): `assessment_id`
- `fk_conflict_learner` (NON-UNIQUE): `learner_id`
- `idx_conflict_reviewer` (NON-UNIQUE): `reviewer_id, is_active`

## reviewers

Instructors and administrators who review integrity cases.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `reviewer_id` | `BIGINT` | No | `` | PK |
| `reviewer_code` | `VARCHAR(30)` | No | `` | UNIQUE |
| `full_name` | `VARCHAR(120)` | No | `` |  |
| `email` | `VARCHAR(150)` | No | `` | UNIQUE |
| `role` | `VARCHAR(30)` | No | `` |  |
| `department` | `VARCHAR(100)` | No | `` |  |
| `max_active_cases` | `INTEGER` | No | `'5'` |  |
| `is_active` | `TINYINT` | No | `'1'` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- No foreign keys.

### Unique constraints

- `email`: `email`
- `reviewer_code`: `reviewer_code`

### Check constraints

- `chk_reviewer_capacity`: `(`max_active_cases` > 0)`
- `chk_reviewer_role`: `(`role` in (_latin1'INSTRUCTOR',_latin1'ADMIN',_latin1'REVIEWER'))`

### Indexes

- `email` (UNIQUE): `email`
- `reviewer_code` (UNIQUE): `reviewer_code`

## similarity_reports

Similarity analysis results generated for submissions.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `report_id` | `VARCHAR(100)` | No | `` | PK |
| `submission_id` | `VARCHAR(40)` | No | `` | FK → submissions.submission_id |
| `evaluated_rule_id` | `VARCHAR(30)` | Yes | `` | FK → integrity_rules.rule_id |
| `similarity_score` | `DECIMAL(5, 2)` | No | `` |  |
| `matched_source_count` | `INTEGER` | No | `'0'` |  |
| `report_category` | `VARCHAR(30)` | No | `` |  |
| `review_action` | `VARCHAR(30)` | No | `` |  |
| `generated_at` | `DATETIME` | No | `` |  |
| `generator_version` | `VARCHAR(30)` | No | `` |  |

### Foreign-key relationships

- `evaluated_rule_id` → `integrity_rules.rule_id`
- `submission_id` → `submissions.submission_id`

### Unique constraints

- No additional unique constraints.

### Check constraints

- `chk_report_category`: `(`report_category` in (_latin1'LOW',_latin1'MODERATE',_latin1'HIGH',_latin1'CRITICAL'))`
- `chk_review_action`: `(`review_action` in (_latin1'NO_FLAG',_latin1'MONITOR',_latin1'REVIEW'))`
- `chk_similarity_score`: `(`similarity_score` between 0 and 100)`

### Indexes

- `fk_report_rule` (NON-UNIQUE): `evaluated_rule_id`
- `idx_report_action` (NON-UNIQUE): `review_action`
- `idx_report_score` (NON-UNIQUE): `similarity_score`
- `idx_report_submission` (NON-UNIQUE): `submission_id`

## submissions

Learner submissions associated with assessments.

### Columns

| Column | Data type | Nullable | Default | Key |
|---|---|---|---|---|
| `submission_id` | `VARCHAR(40)` | No | `` | PK |
| `learner_id` | `BIGINT` | No | `` | FK → learners.learner_id, UNIQUE |
| `assessment_id` | `BIGINT` | No | `` | FK → assessments.assessment_id, UNIQUE |
| `submitted_at` | `DATETIME` | No | `` |  |
| `content_reference` | `VARCHAR(500)` | No | `` |  |
| `content_hash` | `CHAR(64)` | Yes | `` |  |
| `attempt_number` | `INTEGER` | No | `'1'` | UNIQUE |
| `status` | `VARCHAR(30)` | No | `'SUBMITTED'` |  |
| `created_at` | `DATETIME` | No | `CURRENT_TIMESTAMP` |  |

### Foreign-key relationships

- `assessment_id` → `assessments.assessment_id`
- `learner_id` → `learners.learner_id`

### Unique constraints

- `uq_submission_attempt`: `learner_id, assessment_id, attempt_number`

### Check constraints

- `chk_submission_attempt`: `(`attempt_number` > 0)`
- `chk_submission_status`: `(`status` in (_latin1'SUBMITTED',_latin1'PROCESSING',_latin1'ANALYZED',_latin1'REJECTED'))`

### Indexes

- `idx_submission_assessment` (NON-UNIQUE): `assessment_id`
- `idx_submission_date` (NON-UNIQUE): `submitted_at`
- `idx_submission_learner` (NON-UNIQUE): `learner_id`
- `uq_submission_attempt` (UNIQUE): `learner_id, assessment_id, attempt_number`

## Important business rules

1. Similarity scores are indicators for review, not automatic proof of misconduct.
2. Investigation decisions must include reviewer rationale.
3. Reviewer conflicts must be checked before assignment.
4. Appeals require independent review.
5. Historical decisions and case events must remain traceable.
6. Case closure requires a closure timestamp and closure reason.
7. Ground-truth labels are maintained separately from operational database records.
