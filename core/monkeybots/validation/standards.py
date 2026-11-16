"""
MonkeyBots Engineering Validation Standards and Schemas
Defines validation classification standards, analytical tolerances, and report data structures.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    KNOWN_LIMITATION = "KNOWN_LIMITATION"


class ValidationMetric(BaseModel):
    """Specific measurable parameter evaluated against an established analytical reference."""
    name: str = Field(..., description="Metric identifier, e.g. 'position_rmse', 'energy_drift'")
    expected_value: float = Field(..., description="Analytical, mathematical, or independently established expected value")
    actual_value: float = Field(..., description="Simulated or calculated numerical value")
    difference: float = Field(..., description="|actual - expected| absolute error")
    relative_error: Optional[float] = Field(default=None, description="Relative error (|actual - expected| / |expected|)")
    tolerance: float = Field(..., description="Maximum acceptable absolute difference for compliance")
    unit: str = Field(default="", description="Physical unit, e.g. 'm', 'rad', 'J', 'N*s', '%'")
    status: ValidationStatus = Field(default=ValidationStatus.VERIFIED)
    notes: Optional[str] = Field(default=None, description="Technical context, reference formula, or limitation note")


class ValidationTestCase(BaseModel):
    """Complete validation test record conforming to engineering standards."""
    id: str = Field(..., description="Unique test case identifier (e.g. 'VAL_KIN_01')")
    category: str = Field(..., description="Validation category (e.g. 'Model', 'Kinematics', 'Physics')")
    name: str = Field(..., description="Human-readable benchmark title")
    description: str = Field(..., description="Detailed description of the analytical verification procedure")
    standard_reference: str = Field(..., description="Authoritative reference (e.g. 'Euler-Lagrange Mechanics', 'ISO 9283')")
    status: ValidationStatus = Field(default=ValidationStatus.VERIFIED)
    metrics: List[ValidationMetric] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)
    failure_reason: Optional[str] = Field(default=None)


class ValidationSuiteReport(BaseModel):
    """Full engineering validation suite report."""
    suite_name: str = Field(default="MonkeyBots Engineering Validation & Benchmarking Suite")
    version: str = Field(default="1.0.0")
    timestamp: str
    overall_status: ValidationStatus = Field(default=ValidationStatus.VERIFIED)
    total_tests: int = 0
    verified_count: int = 0
    failed_count: int = 0
    known_limitations_count: int = 0
    not_implemented_count: int = 0
    compliance_percentage: float = 0.0
    test_cases: List[ValidationTestCase] = Field(default_factory=list)
    system_info: Dict[str, Any] = Field(default_factory=dict)
