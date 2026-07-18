"""
test_extraction.py — Integration Tests
=======================================
Run with: pytest tests/ -v

These tests verify your extraction schemas work correctly.
Written with GitHub Copilot during Phase 4 of the workshop.
"""

from pathlib import Path

import pytest

from starter.schemas import (
    Claimant,
    ClaimFormExtraction,
    DocumentType,
    Doctor,
    InvoiceExtraction,
    InvoiceItem,
    MedicalReportExtraction,
    PolicyExtraction,
    PoliceReportExtraction,
    Witness,
)


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DOCS = ROOT / "data" / "sample_docs"


# ── Schema Tests ──────────────────────────────────────────────────────────────

class TestClaimant:
    def test_minimal_claimant(self):
        c = Claimant(name="Kofi Asante Boateng")
        assert c.name == "Kofi Asante Boateng"
        assert c.id is None

    def test_full_claimant(self):
        c = Claimant(
            name="Kofi Asante Boateng",
            id="GHA-7731-2019",
            phone="0244 871 332",
            address="House 14, Dansoman, Accra",
            dob="12/04/1985",
        )
        assert c.id == "GHA-7731-2019"
        assert c.phone == "0244 871 332"


class TestClaimFormExtraction:
    def test_claim_with_witness(self):
        claim = ClaimFormExtraction(
            claim_number="CLM-2023-88101",
            claimant=Claimant(name="Kwame Ofori Acheampong", id="GHA-9910-2022"),
            witness=Witness(
                name="Emmanuel Kwesi Tetteh",
                id="GHA-0091-2017",
                phone="0277 001 456",
                address="Madina, Accra",
            ),
        )
        assert claim.witness is not None
        assert claim.witness.phone == "0277 001 456"
        assert claim.document_type == DocumentType.CLAIM_FORM

    def test_claim_without_witness(self):
        claim = ClaimFormExtraction(
            claim_number="CLM-2023-10011",
            claimant=Claimant(name="Kwabena Asare Darkwa"),
        )
        assert claim.witness is None


class TestPolicyExtraction:
    def test_policy_premium(self):
        policy = PolicyExtraction(
            policy_number="NIC-POL-2023-44001",
            insurer="Enterprise Insurance Co. Ltd",
            claimant=Claimant(name="Kofi Asante Boateng"),
            annual_premium=1200.0,
            sum_insured=14400.0,
        )
        assert policy.annual_premium == 1200.0
        assert policy.document_type == DocumentType.POLICY

    def test_policy_coverage_items_and_officer(self):
        policy = PolicyExtraction(
            policy_number="NIC-POL-2023-44001",
            insurer="Star Assurance Company Ltd",
            claimant=Claimant(name="Kofi Asante Boateng"),
            coverage_items=["Hospitalisation & Surgery", "Prescription Drugs"],
            authorised_officer="K. Osei-Bonsu",
        )
        assert len(policy.coverage_items) == 2
        assert policy.authorised_officer == "K. Osei-Bonsu"


class TestInvoiceExtraction:
    def test_invoice_items(self):
        invoice = InvoiceExtraction(
            provider={"name": "MediQuick Services Ltd", "reg": "NIC-PRV-7723"},
            items=[
                InvoiceItem(
                    description="Emergency Consultation",
                    quantity=1,
                    unit_cost=1200.0,
                    total=1200.0,
                ),
                InvoiceItem(
                    description="IV Therapy",
                    quantity=3,
                    unit_cost=850.0,
                    total=2550.0,
                ),
            ],
            total_payable=3750.0,
            authorised_by="J. K. Owusu",
        )
        assert len(invoice.items) == 2
        assert invoice.total_payable == 3750.0
        assert invoice.authorised_by == "J. K. Owusu"


class TestMedicalAndPolice:
    def test_medical_report(self):
        report = MedicalReportExtraction(
            patient=Claimant(name="Kofi Asante Boateng"),
            doctor=Doctor(name="Dr. Kwabena Mensah", reg_number="MDC-GH-04421"),
            diagnosis="Polytrauma from road accident",
            icd10_code="ICD-806",
            presenting_complaints="Patient presented with polytrauma from road accident.",
            medications="See attached prescription",
            billing_provider="MediQuick Services Ltd",
        )
        assert report.document_type == DocumentType.MEDICAL_REPORT
        assert report.doctor.reg_number == "MDC-GH-04421"
        assert report.icd10_code == "ICD-806"

    def test_police_report(self):
        report = PoliceReportExtraction(
            claimant=Claimant(name="Kwame Ofori Acheampong"),
            witness=Witness(name="Emmanuel Kwesi Tetteh", phone="0277 001 456"),
            incident_location="Accra-Tema Motorway",
            incident_time="09:26 hrs",
            incident_type="Road Traffic Accident",
            officer_badge="GPS-8367",
            claim_ref="CLM-2023-88101",
        )
        assert report.document_type == DocumentType.POLICE_REPORT
        assert report.witness.phone == "0277 001 456"
        assert report.officer_badge == "GPS-8367"
        assert report.incident_time == "09:26 hrs"


class TestClaimFormEnrichment:
    def test_claim_insurer_and_declaration_date(self):
        claim = ClaimFormExtraction(
            claim_number="CLM-2023-77001",
            insurer="SIC Insurance Company Ltd",
            claimant=Claimant(name="Kofi Asante Boateng"),
            declaration_date="14/03/2023",
        )
        assert claim.insurer == "SIC Insurance Company Ltd"
        assert claim.declaration_date == "14/03/2023"


class TestDocumentTypes:
    def test_all_document_types_exist(self):
        types = [t.value for t in DocumentType]
        assert "policy" in types
        assert "claim_form" in types
        assert "medical_report" in types
        assert "invoice" in types
        assert "police_report" in types
        assert "unknown" in types

    def test_document_type_from_string(self):
        dt = DocumentType("claim_form")
        assert dt == DocumentType.CLAIM_FORM

    def test_schema_map_covers_extractable_types(self):
        """Every non-UNKNOWN type used in Phase 2 has a Pydantic schema."""
        from starter.schemas import (
            ClaimFormExtraction,
            InvoiceExtraction,
            MedicalReportExtraction,
            PoliceReportExtraction,
            PolicyExtraction,
        )

        schema_map = {
            DocumentType.POLICY: PolicyExtraction,
            DocumentType.CLAIM_FORM: ClaimFormExtraction,
            DocumentType.MEDICAL_REPORT: MedicalReportExtraction,
            DocumentType.INVOICE: InvoiceExtraction,
            DocumentType.POLICE_REPORT: PoliceReportExtraction,
        }
        extractable = {t for t in DocumentType if t != DocumentType.UNKNOWN}
        assert set(schema_map.keys()) == extractable


# ── Sample docs + fraud pattern tests ─────────────────────────────────────────

class TestSampleDocs:
    def test_sample_docs_present(self):
        assert SAMPLE_DOCS.exists(), "data/sample_docs/ is missing"
        pdfs = list(SAMPLE_DOCS.glob("*.pdf"))
        assert len(pdfs) == 36, f"Expected 36 PDFs, found {len(pdfs)}"


class TestFraudPatterns:
    """Test that our synthetic data contains the expected fraud patterns."""

    RING_B_WITNESS_PHONE = "0277 001 456"
    RING_C_PHONE = "0244 512 988"
    RING_A_DOCTOR_REG = "MDC-GH-04421"

    def test_ring_b_ghost_witness_schema(self):
        """Ghost witness should have the same phone across multiple claims."""
        witness = Witness(
            name="Emmanuel Kwesi Tetteh",
            phone=self.RING_B_WITNESS_PHONE,
            id="GHA-0091-2017",
            address="Madina, Accra",
        )
        assert witness.phone == self.RING_B_WITNESS_PHONE

    def test_ring_c_identity_cycling_schema(self):
        """Three claimants with same phone but different names — schema allows this."""
        names = ["Abena Owusu", "A. Owusu", "Abena Owusu-Mensah"]
        claimants = [
            Claimant(name=name, phone=self.RING_C_PHONE)
            for name in names
        ]
        phones = {c.phone for c in claimants}
        assert len(phones) == 1, "All Ring C claimants share one phone number"
        assert len({c.name for c in claimants}) == 3, "But have 3 different names"

    def test_ring_a_doctor_schema(self):
        doctor = Doctor(
            name="Dr. Kwabena Mensah",
            reg_number=self.RING_A_DOCTOR_REG,
            hospital="Mediplus Clinic, Adabraka",
        )
        assert doctor.reg_number == self.RING_A_DOCTOR_REG
