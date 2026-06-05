import json
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.assessment import Assessment
from app.models.assessment_question import AssessmentQuestion
from app.models.assessment_submission import AssessmentSubmission
from app.schemas.assessment_question import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionStudentResponse,
)
from app.schemas.assessment_submission import (
    SubmissionCreate, GradeSubmission, SubmissionResponse, AnswerItem,
)

router = APIRouter(prefix="/api/assessment-questions", tags=["Assessment Questions"])


def _question_to_response(q: AssessmentQuestion) -> dict:
    options = json.loads(q.options) if q.options else []
    return {
        "id": q.id,
        "assessment_id": q.assessment_id,
        "question_text": q.question_text,
        "question_type": q.question_type,
        "options": options,
        "correct_answer": q.correct_answer,
        "marks": q.marks,
        "order": q.order,
        "created_at": q.created_at,
    }


def _question_to_student_response(q: AssessmentQuestion) -> dict:
    options = json.loads(q.options) if q.options else []
    return {
        "id": q.id,
        "assessment_id": q.assessment_id,
        "question_text": q.question_text,
        "question_type": q.question_type,
        "options": options,
        "marks": q.marks,
        "order": q.order,
    }


# ─── Questions CRUD (Lecturer/Admin) ─────────────────────────────────────────


@router.get("", response_model=List[QuestionResponse])
def list_questions(
    assessment_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List questions for an assessment. Lecturers see correct answers, students don't."""
    questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.assessment_id == assessment_id)
        .order_by(AssessmentQuestion.order.asc())
        .all()
    )
    if current_user.role == "student":
        return [_question_to_student_response(q) for q in questions]
    return [_question_to_response(q) for q in questions]


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a question for an assessment."""
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Verify assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == data.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    question = AssessmentQuestion(
        assessment_id=data.assessment_id,
        question_text=data.question_text,
        question_type=data.question_type,
        options=json.dumps(data.options),
        correct_answer=data.correct_answer,
        marks=data.marks,
        order=data.order,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return _question_to_response(question)


@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: str,
    data: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a question."""
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    question = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    if data.question_text is not None:
        question.question_text = data.question_text
    if data.options is not None:
        question.options = json.dumps(data.options)
    if data.correct_answer is not None:
        question.correct_answer = data.correct_answer
    if data.marks is not None:
        question.marks = data.marks
    if data.order is not None:
        question.order = data.order

    db.commit()
    db.refresh(question)
    return _question_to_response(question)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a question."""
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    question = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    db.delete(question)
    db.commit()


# ─── Submissions ──────────────────────────────────────────────────────────────


@router.get("/submissions", response_model=List[SubmissionResponse])
def list_submissions(
    assessment_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List submissions. Lecturers see all; students see only their own."""
    query = db.query(AssessmentSubmission).filter(
        AssessmentSubmission.assessment_id == assessment_id
    )
    if current_user.role == "student":
        query = query.filter(AssessmentSubmission.student_id == current_user.id)

    submissions = query.order_by(AssessmentSubmission.submitted_at.desc()).all()

    results = []
    for sub in submissions:
        answers = json.loads(sub.answers) if sub.answers else []
        results.append({
            "id": sub.id,
            "assessment_id": sub.assessment_id,
            "student_id": sub.student_id,
            "answers": answers,
            "score": sub.score,
            "total_marks": sub.total_marks,
            "is_graded": sub.is_graded,
            "graded_by": sub.graded_by,
            "feedback": sub.feedback,
            "submitted_at": sub.submitted_at,
            "graded_at": sub.graded_at,
        })
    return results


@router.post("/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_assessment(
    data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student submits an assessment attempt. Auto-grades MCQ quizzes."""
    if current_user.role not in ("student", "super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can submit")

    # Verify assessment
    assessment = db.query(Assessment).filter(Assessment.id == data.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    # Check max attempts
    existing_count = (
        db.query(AssessmentSubmission)
        .filter(
            AssessmentSubmission.assessment_id == data.assessment_id,
            AssessmentSubmission.student_id == current_user.id,
        )
        .count()
    )
    if existing_count >= assessment.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum attempts ({assessment.max_attempts}) reached",
        )

    # Get questions for auto-grading
    questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.assessment_id == data.assessment_id)
        .all()
    )

    total_marks = sum(q.marks for q in questions)
    answers_json = json.dumps([a.model_dump() for a in data.answers])

    # Auto-grade if it's a quiz (all MCQ)
    is_quiz = assessment.type == "quiz"
    score = 0
    is_graded = False
    graded_by = None

    if is_quiz and questions:
        # Build lookup: question_id -> correct_answer
        correct_map = {q.id: (q.correct_answer, q.marks) for q in questions}
        for answer in data.answers:
            if answer.question_id in correct_map:
                correct, marks = correct_map[answer.question_id]
                if answer.answer.strip().lower() == correct.strip().lower():
                    score += marks
        is_graded = True
        graded_by = "system"

    submission = AssessmentSubmission(
        assessment_id=data.assessment_id,
        student_id=current_user.id,
        answers=answers_json,
        score=score,
        total_marks=total_marks,
        is_graded=is_graded,
        graded_by=graded_by,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    answers_list = json.loads(submission.answers) if submission.answers else []
    return {
        "id": submission.id,
        "assessment_id": submission.assessment_id,
        "student_id": submission.student_id,
        "answers": answers_list,
        "score": submission.score,
        "total_marks": submission.total_marks,
        "is_graded": submission.is_graded,
        "graded_by": submission.graded_by,
        "feedback": submission.feedback,
        "submitted_at": submission.submitted_at,
        "graded_at": submission.graded_at,
    }


@router.put("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
def grade_submission(
    submission_id: str,
    data: GradeSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lecturer grades a submission (for essay-type assessments)."""
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    submission = db.query(AssessmentSubmission).filter(AssessmentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    submission.score = data.score
    submission.feedback = data.feedback
    submission.is_graded = True
    submission.graded_by = current_user.id
    submission.graded_at = datetime.utcnow()

    db.commit()
    db.refresh(submission)

    answers_list = json.loads(submission.answers) if submission.answers else []
    return {
        "id": submission.id,
        "assessment_id": submission.assessment_id,
        "student_id": submission.student_id,
        "answers": answers_list,
        "score": submission.score,
        "total_marks": submission.total_marks,
        "is_graded": submission.is_graded,
        "graded_by": submission.graded_by,
        "feedback": submission.feedback,
        "submitted_at": submission.submitted_at,
        "graded_at": submission.graded_at,
    }
