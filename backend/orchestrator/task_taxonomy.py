"""
Task Taxonomy System - Business Domain Classification

Defines the authoritative task classification system with:
- Business domains (Marketing, Technology, Operations, Legal, HR, Finance)
- Task characteristics (Creative, Execution, Analysis, Optimization, Management)
- Dynamic field requirements per domain
- Routing rules and constraints
"""

from enum import Enum
from typing import Dict, List, Set, Optional
from dataclasses import dataclass


class BusinessDomain(str, Enum):
    """Primary business domains for task classification."""
    MARKETING = "marketing"
    TECHNOLOGY = "technology"
    OPERATIONS = "operations"
    LEGAL = "legal"
    HR = "hr"
    FINANCE = "finance"


class TaskCharacteristic(str, Enum):
    """Task characteristics that define work nature."""
    CREATIVE = "creative"
    EXECUTION = "execution"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    MANAGEMENT = "management"


@dataclass
class DomainProfile:
    """Configuration for a business domain."""
    domain: BusinessDomain
    display_name: str
    description: str
    color: str  # Hex color for UI
    icon: str  # Icon name
    required_fields: List[str]  # Fields that must be clarified
    optional_fields: List[str]  # Fields that may be clarified
    handlers: List[str]  # Handler types (email, code, content, etc.)
    constraints: Dict[str, any]  # Domain-specific constraints


# Domain Profiles - Authoritative Configuration
DOMAIN_PROFILES: Dict[BusinessDomain, DomainProfile] = {
    BusinessDomain.MARKETING: DomainProfile(
        domain=BusinessDomain.MARKETING,
        display_name="Marketing",
        description="Marketing campaigns, content, and communications",
        color="#2563eb",
        icon="megaphone",
        required_fields=["target_audience", "campaign_type", "tone"],
        optional_fields=["brand_guidelines", "competitor_analysis", "kpis"],
        handlers=["email", "content", "social_media"],
        constraints={
            "max_content_length": 5000,
            "requires_brand_alignment": True,
            "approval_required": True,
        }
    ),
    BusinessDomain.TECHNOLOGY: DomainProfile(
        domain=BusinessDomain.TECHNOLOGY,
        display_name="Technology",
        description="Code, infrastructure, and technical documentation",
        color="#7c3aed",
        icon="code",
        required_fields=["language", "framework", "requirements"],
        optional_fields=["performance_targets", "security_requirements", "testing_strategy"],
        handlers=["code", "documentation", "architecture"],
        constraints={
            "requires_testing": True,
            "requires_code_review": True,
            "security_scan_required": True,
        }
    ),
    BusinessDomain.OPERATIONS: DomainProfile(
        domain=BusinessDomain.OPERATIONS,
        display_name="Operations",
        description="Process optimization, workflows, and procedures",
        color="#059669",
        icon="workflow",
        required_fields=["process_name", "current_state", "desired_outcome"],
        optional_fields=["stakeholders", "timeline", "budget"],
        handlers=["analysis", "documentation", "planning"],
        constraints={
            "requires_stakeholder_review": True,
            "change_management_required": True,
        }
    ),
    BusinessDomain.LEGAL: DomainProfile(
        domain=BusinessDomain.LEGAL,
        display_name="Legal",
        description="Legal documents, compliance, and contracts",
        color="#dc2626",
        icon="scale",
        required_fields=["document_type", "jurisdiction", "parties_involved"],
        optional_fields=["precedents", "compliance_requirements", "risk_assessment"],
        handlers=["documentation", "analysis"],
        constraints={
            "requires_legal_review": True,
            "audit_trail_required": True,
            "version_control_strict": True,
        }
    ),
    BusinessDomain.HR: DomainProfile(
        domain=BusinessDomain.HR,
        display_name="HR",
        description="Human resources, recruitment, and employee management",
        color="#f59e0b",
        icon="users",
        required_fields=["hr_function", "employee_count", "scope"],
        optional_fields=["compliance_requirements", "budget", "timeline"],
        handlers=["documentation", "analysis", "email"],
        constraints={
            "requires_compliance_check": True,
            "confidentiality_required": True,
        }
    ),
    BusinessDomain.FINANCE: DomainProfile(
        domain=BusinessDomain.FINANCE,
        display_name="Finance",
        description="Financial analysis, reporting, and planning",
        color="#10b981",
        icon="trending-up",
        required_fields=["financial_metric", "time_period", "scope"],
        optional_fields=["benchmarks", "assumptions", "sensitivity_analysis"],
        handlers=["analysis", "documentation"],
        constraints={
            "requires_audit": True,
            "data_validation_strict": True,
            "approval_required": True,
        }
    ),
}


class TaskTaxonomy:
    """Manages task classification and routing."""

    @staticmethod
    def get_domain_profile(domain: BusinessDomain) -> DomainProfile:
        """Get configuration for a domain."""
        return DOMAIN_PROFILES[domain]

    @staticmethod
    def get_required_fields(domain: BusinessDomain) -> List[str]:
        """Get required clarification fields for a domain."""
        profile = DOMAIN_PROFILES[domain]
        return profile.required_fields

    @staticmethod
    def get_optional_fields(domain: BusinessDomain) -> List[str]:
        """Get optional clarification fields for a domain."""
        profile = DOMAIN_PROFILES[domain]
        return profile.optional_fields

    @staticmethod
    def get_all_fields(domain: BusinessDomain) -> List[str]:
        """Get all possible fields for a domain."""
        profile = DOMAIN_PROFILES[domain]
        return profile.required_fields + profile.optional_fields

    @staticmethod
    def validate_domain(domain: str) -> bool:
        """Validate if domain is recognized."""
        try:
            BusinessDomain(domain)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_handlers(domain: BusinessDomain) -> List[str]:
        """Get available handlers for a domain."""
        profile = DOMAIN_PROFILES[domain]
        return profile.handlers

    @staticmethod
    def get_constraints(domain: BusinessDomain) -> Dict[str, any]:
        """Get domain-specific constraints."""
        profile = DOMAIN_PROFILES[domain]
        return profile.constraints

    @staticmethod
    def list_domains() -> List[Dict]:
        """List all available domains with metadata."""
        return [
            {
                "value": profile.domain.value,
                "label": profile.display_name,
                "description": profile.description,
                "color": profile.color,
                "icon": profile.icon,
            }
            for profile in DOMAIN_PROFILES.values()
        ]
