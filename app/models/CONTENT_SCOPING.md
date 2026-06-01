# Content Scoping by Intake

## Design Decision

All content (study materials, virtual classes, examinations) is scoped to a specific
**intake + course unit** combination. This means:

- The same course unit "Data Structures" in "Jan 2026 Intake (Year 1)" can have
  completely different materials, classes, and exams than "Data Structures" in
  "Sep 2026 Intake (Year 2)".

- Each intake offering is independent — different lecturers, different content.

## How It Works

The `IntakeUnitAssignment` table is the central link:

```
IntakeUnitAssignment
├── intake_id       → which intake
├── course_unit_id  → which course unit
└── lecturer_id     → who teaches it in this intake
```

All content models reference BOTH `intake_id` AND `course_unit_id`:

```
StudyMaterial
├── intake_id        → scoped to this intake
├── course_unit_id   → for this unit
└── uploaded_by      → by this lecturer

VirtualClass
├── intake_id        → scoped to this intake
├── course_unit_id   → for this unit
└── lecturer_id      → taught by this lecturer

Examination
├── intake_id        → scoped to this intake
├── course_unit_id   → for this unit
└── ...
```

## Query Pattern

To get materials for a student:
1. Find student's enrollment → get intake_id
2. Get courses in that intake → get course_unit_ids
3. Filter materials WHERE intake_id = X AND course_unit_id IN (...)

To get materials for a lecturer:
1. Find IntakeUnitAssignments WHERE lecturer_id = current_user
2. Filter materials WHERE intake_id AND course_unit_id match assignments
