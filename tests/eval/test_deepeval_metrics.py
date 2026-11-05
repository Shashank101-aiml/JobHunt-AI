import os
import json
import pytest
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import FaithfulnessMetric, HallucinationMetric, GEval

from tests.eval.evaluator_model import get_evaluator_judge
from tests.eval.deterministic_validator import validator
from app.services.tailor_service import tailor_resume_content
from app.utils.jd_parser import normalize_jd

DATASET_PATH = os.path.join(os.path.dirname(__file__), "datasets", "synthetic_evaluation_scenarios.json")

@pytest.fixture(scope="module")
def scenarios():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {s["id"]: s for s in data}

@pytest.fixture(scope="module")
def judge_model():
    return get_evaluator_judge()

def test_deepeval_faithfulness_metric_valid_backend(scenarios, judge_model):
    """
    Evaluates faithfulness on Scenario 01 (Senior Backend Engineer).
    Tailored resume must be grounded in original resume and retrieved context.
    """
    sc = scenarios["scenario_01_backend_senior_valid"]
    structured_jd = normalize_jd(sc["job_description"])
    
    result = tailor_resume_content(
        resume_text=sc["candidate_resume"],
        resume_profile={"skills": sc["ground_truth_skills"]},
        structured_jd=structured_jd.model_dump(),
        relevant_chunks=[{"text": "Architected high-throughput REST APIs in FastAPI and PostgreSQL."}],
        before_feedback={"missing_skills": []}
    )

    tailored_text = result["tailored_text"]
    retrieval_context = [
        sc["candidate_resume"][:1000],
        "Architected high-throughput REST APIs in FastAPI and PostgreSQL."
    ]

    test_case = LLMTestCase(
        input=sc["job_description"],
        actual_output=tailored_text,
        expected_output=sc["expected_behavior"],
        retrieval_context=retrieval_context
    )

    metric = FaithfulnessMetric(
        threshold=0.7,
        model=judge_model,
        include_reason=True
    )

    metric.measure(test_case)
    assert metric.score >= metric.threshold, f"Faithfulness score {metric.score} below threshold: {metric.reason}"

def test_deepeval_hallucination_metric_valid_fullstack(scenarios, judge_model):
    """
    Evaluates hallucination detection on Scenario 02 (Full Stack Developer).
    Ensures no invented employers, certifications, or skills are introduced.
    """
    sc = scenarios["scenario_02_fullstack_mid_valid"]
    structured_jd = normalize_jd(sc["job_description"])

    result = tailor_resume_content(
        resume_text=sc["candidate_resume"],
        resume_profile={"skills": sc["ground_truth_skills"]},
        structured_jd=structured_jd.model_dump(),
        relevant_chunks=[],
        before_feedback={"missing_skills": []}
    )

    tailored_text = result["tailored_text"]
    ground_truth_context = [
        sc["candidate_resume"]
    ]

    test_case = LLMTestCase(
        input=sc["job_description"],
        actual_output=tailored_text,
        context=ground_truth_context
    )

    metric = HallucinationMetric(
        threshold=0.7,
        model=judge_model,
        include_reason=True
    )

    metric.measure(test_case)
    assert metric.score >= metric.threshold, f"Hallucination score {metric.score} below threshold: {metric.reason}"

def test_deepeval_geval_job_description_alignment(scenarios, judge_model):
    """
    Evaluates job description alignment using DeepEval G-Eval with custom alignment criteria.
    """
    sc = scenarios["scenario_03_devops_cloud_valid"]
    structured_jd = normalize_jd(sc["job_description"])

    result = tailor_resume_content(
        resume_text=sc["candidate_resume"],
        resume_profile={"skills": sc["ground_truth_skills"]},
        structured_jd=structured_jd.model_dump(),
        relevant_chunks=[{"text": "Managed multi-region AWS infrastructure using Terraform modules."}],
        before_feedback={"missing_skills": []}
    )

    tailored_text = result["tailored_text"]

    alignment_metric = GEval(
        name="Job Description Alignment",
        criteria=(
            "Evaluate whether the tailored resume effectively aligns the candidate's verified skills "
            "with the target job description requirements (AWS, Terraform, Kubernetes, Prometheus) "
            "without fabricating credentials, altering dates, or adding non-existent employers."
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model=judge_model
    )

    test_case = LLMTestCase(
        input=sc["job_description"],
        actual_output=tailored_text,
        expected_output="Tailored resume prominently highlights AWS, Terraform, and Kubernetes experience."
    )

    alignment_metric.measure(test_case)
    assert alignment_metric.score >= alignment_metric.threshold, f"G-Eval alignment score {alignment_metric.score} below threshold: {alignment_metric.reason}"

def test_deepeval_detects_severe_mismatch_alignment(scenarios, judge_model):
    """
    Scenario 14: Embedded C developer applying for React frontend role.
    G-Eval alignment must reflect that the candidate's skills do not align.
    """
    sc = scenarios["scenario_14_mismatch_embedded_to_web"]
    structured_jd = normalize_jd(sc["job_description"])

    result = tailor_resume_content(
        resume_text=sc["candidate_resume"],
        resume_profile={"skills": sc["ground_truth_skills"]},
        structured_jd=structured_jd.model_dump(),
        relevant_chunks=[],
        before_feedback={"missing_skills": ["React", "Next.js", "TypeScript"]}
    )

    tailored_text = result["tailored_text"]

    alignment_metric = GEval(
        name="Job Description Alignment",
        criteria="Assess the degree of technical skill overlap and role suitability.",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model=judge_model
    )

    test_case = LLMTestCase(
        input=sc["job_description"],
        actual_output=tailored_text,
        expected_output="Severe mismatch between Embedded C firmware background and React Frontend expectations."
    )

    alignment_metric.measure(test_case)
    # The score should reflect the mismatch (< 0.7)
    assert alignment_metric.score < 0.7, f"Expected low alignment for severe mismatch, got {alignment_metric.score}"
