"""
Core Domain Models (Batch 1) Tests
===================================

Tests for the initial core domain models:
1. NGO
2. Animal
3. RescueCase

Covers:
- Successful record creation
- Required fields and nullability constraints
- Uniqueness constraints (NGO user_id)
- Foreign-key referential integrity
- SQLAlchemy relationships and back-populates
- Foreign key deletion semantics (RESTRICT on User/NGO, SET NULL on assigned NGO)
- Column synonyms (reported_by_id / assigned_ngo_id)
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models import Role, User, NGO, Animal, RescueCase
from app.models.role import RoleName


class TestCoreModels(unittest.TestCase):
    """Unit and integration tests for NGO, Animal, and RescueCase models."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True

    def setUp(self):
        self.test_id = uuid.uuid4().hex[:8]
        self._created_cases = []
        self._created_animals = []
        self._created_ngos = []
        self._created_users = []

        with self.app.app_context():
            # Ensure standard roles exist and store integer IDs to avoid DetachedInstanceError
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

    def tearDown(self):
        with self.app.app_context():
            db.session.rollback()

            # Clean up in reverse dependency order
            for case_id in self._created_cases:
                c = db.session.get(RescueCase, case_id)
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

    def _create_user(self, role=None, role_id=None, name_suffix=""):
        if role_id is None:
            if role is not None and hasattr(role, "role_id"):
                role_id = role.role_id
            elif role == RoleName.NGO or role == "NGO":
                role_id = self.ngo_role_id
            else:
                role_id = self.user_role_id
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
            description="A test NGO for animal rescue and care",
            location="Test City",
            contact="1234567890",
            verification_status="Verified",
        )
        db.session.add(ngo)
        db.session.commit()
        self._created_ngos.append(ngo.ngo_id)
        return ngo

    # -------------------------------------------------------------------------
    # 1. NGO Model Tests
    # -------------------------------------------------------------------------

    def test_create_ngo_success(self):
        """Verify successful creation of an NGO with all fields and default values."""
        with self.app.app_context():
            ngo_user = self._create_user(role_id=self.ngo_role_id)
            ngo = NGO(
                user_id=ngo_user.user_id,
                name="Paws Protection Society",
                description="Dedicated to rescuing strays",
                location="Sector 12, City",
                contact="+91-9876543210",
            )
            db.session.add(ngo)
            db.session.commit()
            self._created_ngos.append(ngo.ngo_id)

            fetched = db.session.get(NGO, ngo.ngo_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.name, "Paws Protection Society")
            self.assertEqual(fetched.user_id, ngo_user.user_id)
            self.assertEqual(fetched.verification_status, "Unverified")  # Default value
            self.assertEqual(fetched.location, "Sector 12, City")
            self.assertEqual(fetched.contact, "+91-9876543210")
            self.assertIn("Paws Protection Society", repr(fetched))

    def test_ngo_required_name(self):
        """NGO creation fails if name is null."""
        with self.app.app_context():
            ngo_user = self._create_user(role_id=self.ngo_role_id)
            ngo = NGO(
                user_id=ngo_user.user_id,
                name=None,  # Nullable=False
            )
            db.session.add(ngo)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_ngo_required_user_id(self):
        """NGO creation fails if user_id is null."""
        with self.app.app_context():
            ngo = NGO(
                user_id=None,  # Nullable=False
                name="Orphan NGO",
            )
            db.session.add(ngo)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_ngo_user_id_unique(self):
        """A user can only be linked to at most one NGO profile."""
        with self.app.app_context():
            ngo_user = self._create_user(role_id=self.ngo_role_id)
            ngo1 = self._create_ngo(user=ngo_user, name_suffix="First")

            # Attempt to create a second NGO with the same user_id
            ngo2 = NGO(
                user_id=ngo_user.user_id,
                name="Duplicate NGO",
            )
            db.session.add(ngo2)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_ngo_foreign_key_invalid_user(self):
        """NGO creation fails if user_id does not exist."""
        with self.app.app_context():
            ngo = NGO(
                user_id=999999999,  # Non-existent user
                name="Ghost NGO",
            )
            db.session.add(ngo)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_ngo_user_relationship(self):
        """Verify two-way relationship between User and NGO."""
        with self.app.app_context():
            ngo_user = self._create_user(role_id=self.ngo_role_id)
            ngo = self._create_ngo(user=ngo_user)

            # Test back-populates from both directions
            self.assertEqual(ngo.user.user_id, ngo_user.user_id)
            self.assertEqual(ngo_user.ngo.ngo_id, ngo.ngo_id)

    def test_delete_user_restricted_when_ngo_exists(self):
        """A User cannot be deleted while they own an active NGO profile."""
        with self.app.app_context():
            ngo_user = self._create_user(role_id=self.ngo_role_id)
            ngo = self._create_ngo(user=ngo_user)

            user_to_delete = db.session.get(User, ngo_user.user_id)
            db.session.delete(user_to_delete)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    # -------------------------------------------------------------------------
    # 2. Animal Model Tests
    # -------------------------------------------------------------------------

    def test_create_animal_success(self):
        """Verify successful creation of an Animal listing with all fields."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = Animal(
                ngo_id=ngo.ngo_id,
                name="Max",
                species="Dog",
                breed="Golden Retriever",
                age=2,
                gender="Male",
                description="Friendly and energetic",
                location="Koramangala, Bangalore",
                status="Available",
                image_url="https://s3.amazonaws.com/pawconnect/animals/max.jpg",
            )
            db.session.add(animal)
            db.session.commit()
            self._created_animals.append(animal.animal_id)

            fetched = db.session.get(Animal, animal.animal_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.name, "Max")
            self.assertEqual(fetched.species, "Dog")
            self.assertEqual(fetched.breed, "Golden Retriever")
            self.assertEqual(fetched.age, 2)
            self.assertEqual(fetched.gender, "Male")
            self.assertEqual(fetched.status, "Available")
            self.assertEqual(fetched.ngo_id, ngo.ngo_id)
            self.assertIsInstance(fetched.created_at, datetime)
            self.assertIn("Max", repr(fetched))

    def test_animal_minimal_fields_and_defaults(self):
        """An animal can be created with only required fields (species and ngo_id)."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = Animal(
                ngo_id=ngo.ngo_id,
                species="Cat",
            )
            db.session.add(animal)
            db.session.commit()
            self._created_animals.append(animal.animal_id)

            fetched = db.session.get(Animal, animal.animal_id)
            self.assertIsNotNone(fetched)
            self.assertIsNone(fetched.name)
            self.assertEqual(fetched.species, "Cat")
            self.assertIsNone(fetched.breed)
            self.assertIsNone(fetched.age)
            self.assertEqual(fetched.status, "Available")  # Default status
            self.assertIn("Unnamed", repr(fetched))

    def test_animal_required_species(self):
        """Animal creation fails if species is null."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = Animal(
                ngo_id=ngo.ngo_id,
                species=None,  # Nullable=False
            )
            db.session.add(animal)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_animal_required_ngo_id(self):
        """Animal creation fails if ngo_id is null."""
        with self.app.app_context():
            animal = Animal(
                ngo_id=None,  # Nullable=False
                species="Dog",
            )
            db.session.add(animal)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_animal_foreign_key_invalid_ngo(self):
        """Animal creation fails if ngo_id does not exist."""
        with self.app.app_context():
            animal = Animal(
                ngo_id=999999999,
                species="Dog",
            )
            db.session.add(animal)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_animal_ngo_relationship(self):
        """Verify two-way relationship between NGO and Animal listings."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal1 = Animal(ngo_id=ngo.ngo_id, species="Dog", name="Buddy")
            animal2 = Animal(ngo_id=ngo.ngo_id, species="Cat", name="Luna")
            db.session.add_all([animal1, animal2])
            db.session.commit()
            self._created_animals.extend([animal1.animal_id, animal2.animal_id])

            self.assertEqual(animal1.ngo.ngo_id, ngo.ngo_id)
            self.assertEqual(animal2.ngo.ngo_id, ngo.ngo_id)

            fetched_ngo = db.session.get(NGO, ngo.ngo_id)
            animal_ids = [a.animal_id for a in fetched_ngo.animals]
            self.assertIn(animal1.animal_id, animal_ids)
            self.assertIn(animal2.animal_id, animal_ids)

    def test_delete_ngo_restricted_when_animals_exist(self):
        """An NGO cannot be deleted while it has active animal records."""
        with self.app.app_context():
            ngo = self._create_ngo()
            animal = Animal(ngo_id=ngo.ngo_id, species="Dog", name="Rocky")
            db.session.add(animal)
            db.session.commit()
            self._created_animals.append(animal.animal_id)

            ngo_to_delete = db.session.get(NGO, ngo.ngo_id)
            db.session.delete(ngo_to_delete)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    # -------------------------------------------------------------------------
    # 3. RescueCase Model Tests
    # -------------------------------------------------------------------------

    def test_create_rescue_case_unassigned_success(self):
        """Verify successful creation of a RescueCase with initial unassigned state."""
        with self.app.app_context():
            reporter = self._create_user(name_suffix="Reporter")
            case = RescueCase(
                reported_by=reporter.user_id,
                animal_type="Dog",
                condition="Injured hind leg",
                location="Main Market, Sector 14",
                description="Hit by bicycle, limping",
                urgency="High",
                image_url="https://s3.amazonaws.com/pawconnect/cases/c1.jpg",
            )
            db.session.add(case)
            db.session.commit()
            self._created_cases.append(case.case_id)

            fetched = db.session.get(RescueCase, case.case_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.reported_by, reporter.user_id)
            self.assertEqual(fetched.reported_by_id, reporter.user_id)  # Synonym check
            self.assertIsNone(fetched.assigned_ngo)
            self.assertIsNone(fetched.assigned_ngo_id)  # Synonym check
            self.assertEqual(fetched.status, "Reported")  # Default status
            self.assertEqual(fetched.urgency, "High")
            self.assertIsInstance(fetched.created_at, datetime)
            self.assertIsInstance(fetched.updated_at, datetime)
            self.assertIn("Reported", repr(fetched))

    def test_rescue_case_required_location(self):
        """RescueCase creation fails if location is null."""
        with self.app.app_context():
            reporter = self._create_user()
            case = RescueCase(
                reported_by=reporter.user_id,
                location=None,  # Nullable=False
            )
            db.session.add(case)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_rescue_case_required_reporter(self):
        """RescueCase creation fails if reported_by is null."""
        with self.app.app_context():
            case = RescueCase(
                reported_by=None,  # Nullable=False
                location="Somewhere",
            )
            db.session.add(case)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_rescue_case_foreign_key_invalid_reporter(self):
        """RescueCase creation fails if reported_by user does not exist."""
        with self.app.app_context():
            case = RescueCase(
                reported_by=999999999,
                location="Somewhere",
            )
            db.session.add(case)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_rescue_case_relationships_and_assignment(self):
        """Verify reporter and assigned NGO relationships on RescueCase."""
        with self.app.app_context():
            reporter = self._create_user(name_suffix="Reporter")
            ngo = self._create_ngo()

            case = RescueCase(
                reported_by=reporter.user_id,
                assigned_ngo=ngo.ngo_id,
                location="Near park gate",
                status="NGO Assigned",
            )
            db.session.add(case)
            db.session.commit()
            self._created_cases.append(case.case_id)

            # Test relationship navigation
            self.assertEqual(case.reporter.user_id, reporter.user_id)
            self.assertEqual(case.ngo.ngo_id, ngo.ngo_id)

            # Test back-references
            self.assertIn(case.case_id, [c.case_id for c in reporter.rescue_cases])
            self.assertIn(case.case_id, [c.case_id for c in ngo.assigned_cases])

    def test_delete_user_restricted_when_reporting_case(self):
        """A User cannot be deleted while they are the reporter of a rescue case."""
        with self.app.app_context():
            reporter = self._create_user(name_suffix="Reporter")
            case = RescueCase(
                reported_by=reporter.user_id,
                location="Central Square",
            )
            db.session.add(case)
            db.session.commit()
            self._created_cases.append(case.case_id)

            user_to_delete = db.session.get(User, reporter.user_id)
            db.session.delete(user_to_delete)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_delete_assigned_ngo_sets_null_on_rescue_case(self):
        """Deleting an assigned NGO sets assigned_ngo to NULL (preserving case history)."""
        with self.app.app_context():
            reporter = self._create_user(name_suffix="Reporter")
            ngo = self._create_ngo(name_suffix="Temp NGO")
            ngo_id = ngo.ngo_id

            case = RescueCase(
                reported_by=reporter.user_id,
                assigned_ngo=ngo_id,
                location="Station Road",
                status="NGO Assigned",
            )
            db.session.add(case)
            db.session.commit()
            self._created_cases.append(case.case_id)

            # Delete the NGO
            ngo_to_delete = db.session.get(NGO, ngo_id)
            db.session.delete(ngo_to_delete)
            db.session.commit()
            # Remove from tracking since it's already deleted
            self._created_ngos.remove(ngo_id)

            # Refresh case from DB and verify assigned_ngo is now NULL
            db.session.expire_all()
            fetched_case = db.session.get(RescueCase, case.case_id)
            self.assertIsNotNone(fetched_case)
            self.assertIsNone(fetched_case.assigned_ngo)
            self.assertIsNone(fetched_case.assigned_ngo_id)
            self.assertIsNone(fetched_case.ngo)


if __name__ == "__main__":
    unittest.main()
