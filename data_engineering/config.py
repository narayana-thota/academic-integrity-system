# Configuration and Constants
SEED = 20261022

# Volume Parameters
TOTAL_LEARNERS = 2000
TOTAL_ASSESSMENTS = 100
TOTAL_REVIEWERS = 30
TOTAL_SUBMISSIONS = 10000
TOTAL_FLAGS = 1000
TOTAL_CASES = 300

# System Parameters
GENERATOR_VERSION = "1.0.0"
OUTPUT_DIRECTORY = "data_engineering/output"

# Deterministic ID Prefixes
# All generated IDs must be reproducible across multiple runs.
ID_PREFIXES = {
    "learner": "LRN",
    "assessment": "ASM",
    "submission": "SUB",
    "report": "RPT",
    "case": "CAS",
    "reviewer": "REV",
    "evidence": "EVD"
}