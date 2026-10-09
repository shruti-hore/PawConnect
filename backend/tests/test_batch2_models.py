"""
Core Domain Models (Batch 2) Tests
===================================

Tests for the Batch 2 domain models:
1. AdoptionApplication
2. Donation
3. VolunteerApplication

Covers:
- Valid record creation and defaults
- Required and nullable fields
- Foreign-key referential integrity
- SQLAlchemy relationships and back-populates
- Foreign key deletion semantics (RESTRICT on user/ngo/animal, SET NULL on donation rescue case)
- Financial integrity (Decimal amounts, no payment credential storage)
"""

import sys
import uuid
from decimal import Decimal
from datetime import datetime
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models import (
    Role,
    User,
    NGO,
    Animal,
    RescueCase,
    AdoptionApplication,
    Donation,
    VolunteerApplication,
)
from app.models.role import RoleName


class TestBatch2Models(unittest.TestCase):
    """Unit and integration tests for AdoptionApplication, Donation, and VolunteerApplication."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True

    def setUp(self):
        self.test_id = uuid.uuid4().hex[:8]
        self._created_adoptions = []
        self._created_donations = []
        self._created_volunteers = []
        self._created_cases = []
        self._created_animals = []
        self._created_ngos = []
        self._created_users = []

        with self.app.app_context():
            user_role = Role.query.filter_by(role_name=RoleName.USER).first()
            if not user_role:
                user_role = Role(role_name=RoleName.USER)
                db.session.add(user_role)
                db.session.commit()
            self.user_role_id = user_role.role_id

            ngo_role = Role.query.filter_by(role_name=RoleName.NGO).first()
            if not ngo_role:
                ngo_role = Role(role_name=RoleName.NGO)
                db.session.add(ngo_role)
                db.session.commit()
            self.ngo_role_id = ngo_role.role_id

            rescuer_role = Role.query.filter_by(role_name=RoleName.RESCUER).first()
            if not rescuer_role:
                rescuer_role = Role(role_name=RoleName.RESCUER)
                db.session.add(rescuer_role)
                db.session.commit()
            self.rescuer_role_id = rescuer_role.role_id

    def tearDown(self):
        with self.app.app_context():
            db.session.rollback()

            # Clean up in reverse dependency order
            for a_id in self._created_adoptions:
                app_obj = db.session.get(AdoptionApplication, a_id)
                if app_obj:
                    db.session.delete(app_obj)
            db.session.commit()

            for d_id in self._created_donations:
                d = db.session.get(Donation, d_id)
                if d:
                    db.session.delete(d)
            db.session.commit()

            for v_id in self._created_volunteers:
                v = db.session.get(VolunteerApplication, v_id)
                if v:
                    db.session.delete(v)
            db.session.commit()

            for c_id in self._created_cases:
                c = db.session.get(RescueCase, c_id)
                if c:
                    db.session.delete(c)
            db.session.commit()

            for animal_id in self._created_animals:
                a = db.session.get(Animal, animal_id)
                if a:
                    db.session.delete(a)
            db.session.commit()

            for ngo_id in self._created_ngos:
                n = db.session.get(NGO, ngo_id)
                if n:
                    db.session.delete(n)
            db.session.commit()

            for user_id in self._created_users:
                u = db.session.get(User, user_id)
                if u:
                    db.session.delete(u)
            db.session.commit()

    def _create_user(self, role_id=None, name_suffix=""):
        role_id = role_id or self.user_role_id
        user = User(
            name=f"Test User {self.test_id} {name_suffix}".strip(),
            email=f"test_{self.test_id}_{uuid.uuid4().hex[:6]}@example.com",
            role_id=role_id,
            auth_id=f"sub-{self.test_id}-{uuid.uuid4().hex[:6]}",
        )
        db.session.add(user)
        db.session.commit()
        self._created_users.append(user.user_id)
        return user

    def _create_ngo(self, user=None, name_suffix=""):
        if user is None:
            user = self._create_user(role_id=self.ngo_role_id, name_suffix="NGO Owner")
        ngo = NGO(
            user_id=user.user_id,
            name=f"Test NGO {self.test_id} {name_suffix}".strip(),
            description="A test NGO for animal welfare",
            location="Test City",
            contact="1234567890",
            verification_status="Verified",
        )
        db.session.add(ngo)
        db.session.commit()
        self._created_ngos.append(ngo.ngo_id)
        return ngo

    def _create_animal(self, ngo=None, name_suffix=""):
        if ngo is None:
            ngo = self._create_ngo()
        animal = Animal(
            ngo_id=ngo.ngo_id,
            name=f"Test Pet {self.test_id} {name_suffix}".strip(),
            species="Dog",
            breed="Labrador",
            age=3,
            status="Available",
        )
        db.session.add(animal)
        db.session.commit()
        self._created_animals.append(animal.animal_id)
        return animal

    def _create_rescue_case(self, reporter=None):
        if reporter is None:
            reporter = self._create_user(name_suffix="Reporter")
        case = RescueCase(
            reported_by=reporter.user_id,
            animal_type="Cat",
            location="Sector 18",
            condition="Mild injury",
            status="Reported",
        )
        db.session.add(case)
        db.session.commit()
        self._created_cases.append(case.case_id)
        return case

    # -------------------------------------------------------------------------
    # 1. AdoptionApplication Tests
    # -------------------------------------------------------------------------

    def test_create_adoption_application_success(self):
        """Verify successful creation of an AdoptionApplication with default status."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = self._create_animal(ngo=ngo)
            applicant = self._create_user(name_suffix="Adopter")

            application = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=applicant.user_id,
                ngo_id=ngo.ngo_id,
                message="We have a spacious backyard and would love to adopt Max.",
            )
            db.session.add(application)
            db.session.commit()
            self._created_adoptions.append(application.application_id)

            fetched = db.session.get(AdoptionApplication, application.application_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.animal_id, animal.animal_id)
            self.assertEqual(fetched.user_id, applicant.user_id)
            self.assertEqual(fetched.ngo_id, ngo.ngo_id)
            self.assertEqual(fetched.status, "Pending")  # Default status
            self.assertEqual(fetched.message, "We have a spacious backyard and would love to adopt Max.")
            self.assertIsInstance(fetched.application_date, datetime)
            self.assertIn("Pending", repr(fetched))

    def test_adoption_application_required_fields(self):
        """AdoptionApplication fails if any required foreign key is null."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = self._create_animal(ngo=ngo)
            applicant = self._create_user()

            # Missing animal_id
            app_no_animal = AdoptionApplication(
                animal_id=None,
                user_id=applicant.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(app_no_animal)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # Missing user_id
            app_no_user = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=None,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(app_no_user)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # Missing ngo_id
            app_no_ngo = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=applicant.user_id,
                ngo_id=None,
            )
            db.session.add(app_no_ngo)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_adoption_application_optional_message(self):
        """AdoptionApplication succeeds with message as None."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = self._create_animal(ngo=ngo)
            applicant = self._create_user()

            application = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=applicant.user_id,
                ngo_id=ngo.ngo_id,
                message=None,
            )
            db.session.add(application)
            db.session.commit()
            self._created_adoptions.append(application.application_id)

            fetched = db.session.get(AdoptionApplication, application.application_id)
            self.assertIsNotNone(fetched)
            self.assertIsNone(fetched.message)

    def test_adoption_application_foreign_key_integrity(self):
        """AdoptionApplication fails when foreign keys do not exist."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = self._create_animal(ngo=ngo)
            applicant = self._create_user()

            # Non-existent animal
            invalid_animal_app = AdoptionApplication(
                animal_id=999999999,
                user_id=applicant.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(invalid_animal_app)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # Non-existent user
            invalid_user_app = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=999999999,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(invalid_user_app)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # Non-existent NGO
            invalid_ngo_app = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=applicant.user_id,
                ngo_id=999999999,
            )
            db.session.add(invalid_ngo_app)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_adoption_application_relationships(self):
        """Verify relationships from AdoptionApplication to Animal, User, and NGO."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = self._create_animal(ngo=ngo)
            applicant = self._create_user()

            application = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=applicant.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(application)
            db.session.commit()
            self._created_adoptions.append(application.application_id)

            # Test forward navigation
            self.assertEqual(application.animal.animal_id, animal.animal_id)
            self.assertEqual(application.user.user_id, applicant.user_id)
            self.assertEqual(application.ngo.ngo_id, ngo.ngo_id)

            # Test back-references
            self.assertIn(application.application_id, [a.application_id for a in animal.adoption_applications])
            self.assertIn(application.application_id, [a.application_id for a in applicant.adoption_applications])
            self.assertIn(application.application_id, [a.application_id for a in ngo.adoption_applications])

    def test_delete_animal_restricted_when_adoption_exists(self):
        """An animal cannot be deleted when it has active adoption applications (RESTRICT)."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = self._create_animal(ngo=ngo)
            applicant = self._create_user()

            application = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=applicant.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(application)
            db.session.commit()
            self._created_adoptions.append(application.application_id)

            animal_to_del = db.session.get(Animal, animal.animal_id)
            db.session.delete(animal_to_del)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_delete_user_restricted_when_adoption_exists(self):
        """A user cannot be deleted when they have submitted adoption applications (RESTRICT)."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = self._create_animal(ngo=ngo)
            applicant = self._create_user()

            application = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=applicant.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(application)
            db.session.commit()
            self._created_adoptions.append(application.application_id)

            user_to_del = db.session.get(User, applicant.user_id)
            db.session.delete(user_to_del)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_delete_ngo_restricted_when_adoption_exists(self):
        """An NGO cannot be deleted when it has adoption applications (RESTRICT)."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = self._create_animal(ngo=ngo)
            applicant = self._create_user()

            application = AdoptionApplication(
                animal_id=animal.animal_id,
                user_id=applicant.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(application)
            db.session.commit()
            self._created_adoptions.append(application.application_id)

            ngo_to_del = db.session.get(NGO, ngo.ngo_id)
            db.session.delete(ngo_to_del)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    # -------------------------------------------------------------------------
    # 2. Donation Tests
    # -------------------------------------------------------------------------

    def test_create_donation_for_case_success(self):
        """Verify successful creation of a donation linked to a rescue case."""
        with self.app.app_context():
            donor = self._create_user(name_suffix="Donor")
            case = self._create_rescue_case()

            donation = Donation(
                donor_id=donor.user_id,
                case_id=case.case_id,
                amount=Decimal("150.50"),
                payment_status="Completed",
            )
            db.session.add(donation)
            db.session.commit()
            self._created_donations.append(donation.donation_id)

            fetched = db.session.get(Donation, donation.donation_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.donor_id, donor.user_id)
            self.assertEqual(fetched.case_id, case.case_id)
            self.assertEqual(fetched.amount, Decimal("150.50"))
            self.assertEqual(fetched.payment_status, "Completed")
            self.assertIsInstance(fetched.donated_at, datetime)
            self.assertIn("150.50", repr(fetched))

    def test_create_general_donation_without_case(self):
        """A general donation can be made without being linked to a specific case (case_id=None)."""
        with self.app.app_context():
            donor = self._create_user(name_suffix="General Donor")

            donation = Donation(
                donor_id=donor.user_id,
                case_id=None,
                amount=Decimal("50.00"),
            )
            db.session.add(donation)
            db.session.commit()
            self._created_donations.append(donation.donation_id)

            fetched = db.session.get(Donation, donation.donation_id)
            self.assertIsNotNone(fetched)
            self.assertIsNone(fetched.case_id)
            self.assertEqual(fetched.payment_status, "Pending")  # Default status
            self.assertEqual(fetched.amount, Decimal("50.00"))

    def test_donation_required_fields(self):
        """Donation fails if donor_id or amount is null."""
        with self.app.app_context():
            donor = self._create_user()

            # Missing donor_id
            d_no_donor = Donation(
                donor_id=None,
                amount=Decimal("25.00"),
            )
            db.session.add(d_no_donor)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # Missing amount
            d_no_amount = Donation(
                donor_id=donor.user_id,
                amount=None,
            )
            db.session.add(d_no_amount)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_donation_foreign_key_integrity(self):
        """Donation fails when foreign keys do not exist."""
        with self.app.app_context():
            donor = self._create_user()

            # Non-existent donor
            invalid_donor_d = Donation(
                donor_id=999999999,
                amount=Decimal("100.00"),
            )
            db.session.add(invalid_donor_d)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # Non-existent case
            invalid_case_d = Donation(
                donor_id=donor.user_id,
                case_id=999999999,
                amount=Decimal("100.00"),
            )
            db.session.add(invalid_case_d)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_donation_relationships(self):
        """Verify relationships between Donation and User (donor) and RescueCase."""
        with self.app.app_context():
            donor = self._create_user(name_suffix="Donor")
            case = self._create_rescue_case()

            donation = Donation(
                donor_id=donor.user_id,
                case_id=case.case_id,
                amount=Decimal("75.00"),
            )
            db.session.add(donation)
            db.session.commit()
            self._created_donations.append(donation.donation_id)

            # Test forward navigation
            self.assertEqual(donation.donor.user_id, donor.user_id)
            self.assertEqual(donation.rescue_case.case_id, case.case_id)

            # Test back-references
            self.assertIn(donation.donation_id, [d.donation_id for d in donor.donations])
            self.assertIn(donation.donation_id, [d.donation_id for d in case.donations])

    def test_delete_user_restricted_when_donation_exists(self):
        """A user cannot be deleted when financial donation records exist (RESTRICT)."""
        with self.app.app_context():
            donor = self._create_user(name_suffix="Donor")
            donation = Donation(
                donor_id=donor.user_id,
                amount=Decimal("100.00"),
            )
            db.session.add(donation)
            db.session.commit()
            self._created_donations.append(donation.donation_id)

            donor_to_del = db.session.get(User, donor.user_id)
            db.session.delete(donor_to_del)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_delete_rescue_case_sets_null_on_donation(self):
        """Deleting a rescue case sets donation.case_id to NULL (SET NULL), preserving audit history."""
        with self.app.app_context():
            reporter = self._create_user(name_suffix="Reporter")
            donor = self._create_user(name_suffix="Donor")
            case = self._create_rescue_case(reporter=reporter)
            case_id = case.case_id

            donation = Donation(
                donor_id=donor.user_id,
                case_id=case_id,
                amount=Decimal("200.00"),
            )
            db.session.add(donation)
            db.session.commit()
            self._created_donations.append(donation.donation_id)

            # Delete the rescue case
            case_to_del = db.session.get(RescueCase, case_id)
            db.session.delete(case_to_del)
            db.session.commit()
            # Remove from tracking since already deleted
            self._created_cases.remove(case_id)

            db.session.expire_all()
            fetched_donation = db.session.get(Donation, donation.donation_id)
            self.assertIsNotNone(fetched_donation)
            self.assertIsNone(fetched_donation.case_id)
            self.assertIsNone(fetched_donation.rescue_case)
            self.assertEqual(fetched_donation.amount, Decimal("200.00"))

    # -------------------------------------------------------------------------
    # 3. VolunteerApplication Tests
    # -------------------------------------------------------------------------

    def test_create_volunteer_application_success(self):
        """Verify successful creation of a VolunteerApplication with default status."""
        with self.app.app_context():
            volunteer_user = self._create_user(name_suffix="Volunteer")
            ngo = self._create_ngo()

            application = VolunteerApplication(
                user_id=volunteer_user.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(application)
            db.session.commit()
            self._created_volunteers.append(application.volunteer_id)

            fetched = db.session.get(VolunteerApplication, application.volunteer_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.user_id, volunteer_user.user_id)
            self.assertEqual(fetched.ngo_id, ngo.ngo_id)
            self.assertEqual(fetched.status, "Pending")  # Default status
            self.assertIsInstance(fetched.applied_at, datetime)
            self.assertIn("Pending", repr(fetched))

    def test_volunteer_application_required_fields(self):
        """VolunteerApplication fails if user_id or ngo_id is null."""
        with self.app.app_context():
            volunteer_user = self._create_user()
            ngo = self._create_ngo()

            # Missing user_id
            v_no_user = VolunteerApplication(
                user_id=None,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(v_no_user)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # Missing ngo_id
            v_no_ngo = VolunteerApplication(
                user_id=volunteer_user.user_id,
                ngo_id=None,
            )
            db.session.add(v_no_ngo)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_volunteer_application_foreign_key_integrity(self):
        """VolunteerApplication fails when foreign keys do not exist."""
        with self.app.app_context():
            volunteer_user = self._create_user()
            ngo = self._create_ngo()

            # Non-existent user
            v_invalid_user = VolunteerApplication(
                user_id=999999999,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(v_invalid_user)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            # Non-existent NGO
            v_invalid_ngo = VolunteerApplication(
                user_id=volunteer_user.user_id,
                ngo_id=999999999,
            )
            db.session.add(v_invalid_ngo)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_volunteer_application_relationships(self):
        """Verify relationships between VolunteerApplication and User and NGO."""
        with self.app.app_context():
            volunteer_user = self._create_user(name_suffix="Volunteer")
            ngo = self._create_ngo()

            application = VolunteerApplication(
                user_id=volunteer_user.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(application)
            db.session.commit()
            self._created_volunteers.append(application.volunteer_id)

            # Test forward navigation
            self.assertEqual(application.user.user_id, volunteer_user.user_id)
            self.assertEqual(application.ngo.ngo_id, ngo.ngo_id)

            # Test back-references
            self.assertIn(application.volunteer_id, [v.volunteer_id for v in volunteer_user.volunteer_applications])
            self.assertIn(application.volunteer_id, [v.volunteer_id for v in ngo.volunteer_applications])

    def test_delete_user_restricted_when_volunteer_application_exists(self):
        """A user cannot be deleted when they have volunteer applications (RESTRICT)."""
        with self.app.app_context():
            volunteer_user = self._create_user(name_suffix="Volunteer")
            ngo = self._create_ngo()

            application = VolunteerApplication(
                user_id=volunteer_user.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(application)
            db.session.commit()
            self._created_volunteers.append(application.volunteer_id)

            user_to_del = db.session.get(User, volunteer_user.user_id)
            db.session.delete(user_to_del)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_delete_ngo_restricted_when_volunteer_application_exists(self):
        """An NGO cannot be deleted when it has volunteer applications (RESTRICT)."""
        with self.app.app_context():
            volunteer_user = self._create_user(name_suffix="Volunteer")
            ngo = self._create_ngo()

            application = VolunteerApplication(
                user_id=volunteer_user.user_id,
                ngo_id=ngo.ngo_id,
            )
            db.session.add(application)
            db.session.commit()
            self._created_volunteers.append(application.volunteer_id)

            ngo_to_del = db.session.get(NGO, ngo.ngo_id)
            db.session.delete(ngo_to_del)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()


if __name__ == "__main__":
    unittest.main()
