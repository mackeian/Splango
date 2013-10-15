from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TransactionTestCase
from django.test.utils import override_settings

from splango.models import Experiment, GoalRecord
from splango.tests import (
    create_goal, create_goal_record, create_subject, create_enrollment,
    create_experiment, create_variant)


class GoalTest(TransactionTestCase):

    def setUp(self):
        self.subject1 = create_subject()
        self.subject2 = create_subject()
        self.subject3 = create_subject()
        self.subject4 = create_subject()

        self.exp = create_experiment()
        self.variant1 = create_variant(name='variant1', experiment=self.exp)
        self.variant2 = create_variant(name='variant2', experiment=self.exp)
        self.variant3 = create_variant(name='variant3', experiment=self.exp)
        self.variant4 = create_variant(name='variant4', experiment=self.exp)

        # create some enrollments
        create_enrollment(variant=self.variant4, experiment=self.exp)
        create_enrollment(variant=self.variant4, experiment=self.exp)
        create_enrollment(variant=self.variant1, experiment=self.exp)
        create_enrollment(variant=self.variant2, experiment=self.exp)
        create_enrollment(variant=self.variant4, experiment=self.exp)
        create_enrollment(
            variant=self.variant1, subject=self.subject1, experiment=self.exp)
        create_enrollment(
            variant=self.variant1, subject=self.subject2, experiment=self.exp)
        create_enrollment(
            variant=self.variant2, subject=self.subject3, experiment=self.exp)
        create_enrollment(
            variant=self.variant2, subject=self.subject4, experiment=self.exp)
        self.e01 = create_enrollment(
            variant=self.variant3, experiment=self.exp)
        self.e02 = create_enrollment(
            variant=self.variant4, experiment=self.exp)
        self.e03 = create_enrollment(
            variant=self.variant4, experiment=self.exp)
        self.e04 = create_enrollment(
            variant=self.variant4, experiment=self.exp)

        self.subject01 = self.e01.subject
        self.subject02 = self.e02.subject
        self.subject03 = self.e03.subject
        self.subject04 = self.e04.subject

        self.goal1 = create_goal(name='gol1')

    def test_get_records_total(self):
        # create 8 goal records
        create_goal_record(goal=self.goal1, subject=self.subject1)
        create_goal_record(goal=self.goal1, subject=self.subject2)
        create_goal_record(goal=self.goal1, subject=self.subject3)
        create_goal_record(goal=self.goal1, subject=self.subject4)

        create_goal_record(goal=self.goal1, subject=self.subject01)
        create_goal_record(goal=self.goal1, subject=self.subject02)
        create_goal_record(goal=self.goal1, subject=self.subject03)
        gr1 = create_goal_record(goal=self.goal1, subject=self.subject04)

        # are really 8 goal records?
        self.assertEqual(8, self.goal1.get_records_total(self.exp))

        # it is really a GoalRecord?
        self.assertIsInstance(gr1, GoalRecord)

    def test_get_records_count_per_variant(self):
        experiment = self.exp
        goal1 = self.goal1

        # there are no goal records yet
        self.assertEqual(0, goal1.get_records_count_per_variant(experiment))

        # create 8 goal records
        create_goal_record(goal=goal1, subject=self.subject1)
        create_goal_record(goal=goal1, subject=self.subject2)
        create_goal_record(goal=goal1, subject=self.subject3)
        create_goal_record(goal=goal1, subject=self.subject4)

        create_goal_record(goal=goal1, subject=self.subject01)
        create_goal_record(goal=goal1, subject=self.subject02)
        create_goal_record(goal=goal1, subject=self.subject03)
        gr1 = create_goal_record(goal=goal1, subject=self.subject04)

        # now there are 8 goal records!
        self.assertEqual(8, goal1.get_records_total(experiment))

        # verify is a dict
        self.assertIsInstance(
            goal1.get_records_count_per_variant(experiment), dict)

        # that dict has 4 elements, the same of the variants count
        self.assertEqual(
            len(experiment.get_variants()),
            len(goal1.get_records_count_per_variant(experiment)))

        test_dict = goal1.get_records_count_per_variant(experiment)

        # variant1: 2 times, 25.0% of 8 enrollments
        # variant2: 2 times, 25.0% of 8 enrollments
        # variant3: 1 time,  12.5% of 8 enrollments
        # variant4: 3 times, 37.5% of 8 enrollments
        # the expected result, the above given, is:
        # {1: (2, 25.0), 2: (2, 25.0), 3: (1, 12.5), 4: (3, 37.5)}
        expected_dict = {
            self.variant1.pk: (2, 25.0),
            self.variant2.pk: (2, 25.0),
            self.variant3.pk: (1, 12.5),
            self.variant4.pk: (3, 37.5)
        }
        self.assertEquals(expected_dict, test_dict)


class SubjectTest(TransactionTestCase):

    pass


class GoalRecordTest(TransactionTestCase):

    def test_unique_together(self):
        goal = create_goal()
        subject = create_subject()
        create_goal_record(goal=goal, subject=subject)

        self.assertRaises(
            IntegrityError, create_goal_record, goal=goal, subject=subject)


class EnrollmentTest(TransactionTestCase):

    def setUp(self):
        self.variant = create_variant()
        self.subject = create_subject()
        self.experiment = self.variant.experiment

    def test_unique_together(self):
        var = self.variant
        subject = self.subject
        create_enrollment(
            variant=var, subject=subject, experiment=var.experiment)

        self.assertRaises(
            IntegrityError, create_enrollment, variant=var, subject=subject)

    def test_unicode(self):
        var = self.variant
        subject = self.subject
        enrollment = create_enrollment(
            variant=var, subject=subject, experiment=var.experiment)

        self.assertEqual(
            "experiment 'My experiment' subject #1 -- variant A variant",
            enrollment.__unicode__())

    def test_experiment(self):
        var = self.variant
        subject = self.subject

        enrollment = create_enrollment(variant=var, subject=subject,
                                       experiment=var.experiment)

        self.assertIsInstance(enrollment.experiment, Experiment)


class ExperimentTest(TransactionTestCase):
    def setUp(self):
        self.module_name = __name__
        self.variant = create_variant()
        self.subject = create_subject()
        self.experiment = self.variant.experiment
        super(ExperimentTest, self).setUp()

    @override_settings(SPLANGO_EXCLUDE_USER_COMPARISON=None)
    def test_get_or_create_enrollment_not_excluding_by_default(self):
        # Arrange

        # Act
        enrollment = self.experiment.get_or_create_enrollment(self.subject)

        # Assert
        self.assertEquals(self.variant, enrollment.variant)

    def test_get_or_create_enrollment_excludes_admin_user(self):
        # Arrange
        user = get_user_model().objects.create(username='admin')
        subject = create_subject()
        subject.registered_as = user

        function_path = self.module_name + '.my_admin_excluding_comparison'

        # Act
        with override_settings(SPLANGO_EXCLUDE_USER_COMPARISON=function_path):
            enrollment = self.experiment.get_or_create_enrollment(subject)

            # Assert
            self.assertEquals(None, enrollment, 'Excluded user should not be enrolled')

    def test_get_or_create_enrollment_excludes_anonymous_users(self):
        # Arrange
        function_path = self.module_name + '.my_anonymous_excluding_comparison'

        # Act
        with override_settings(SPLANGO_EXCLUDE_USER_COMPARISON=function_path):
            enrollment = self.experiment.get_or_create_enrollment(self.subject)

            # Assert
            self.assertEquals(None, enrollment, 'Anonymous user should not be enrolled')

    def test_get_or_create_enrollment_force_variant(self):
        # Arrange
        exp = create_experiment(name='My Exp 1')
        variant_1 = create_variant(name="v1", experiment=exp)
        variant_2 = create_variant(name="v2", experiment=exp)
        variant_3 = create_variant(name="v2", experiment=exp)

        company_subject = create_subject()
        company_user = get_user_model().objects.create(username='company_user1')
        company_user.company = 'IBM'
        company_subject.registered_as = company_user

        function_path = self.module_name + '.force_variant_user_comparison'

        # Act
        with override_settings(SPLANGO_FORCE_VARIANT_USER_COMPARISON=function_path):
            enrollment_company = exp.get_or_create_enrollment(company_subject, variant_3)

            # Assert
            self.assertEquals(variant_1, enrollment_company.variant, 'Company user should get first variant')


def my_admin_excluding_comparison(user):
    return True if user and user.username == 'admin' else False


def my_anonymous_excluding_comparison(auth_user):
    should_exclude = True if auth_user is None else True
    return should_exclude


def force_variant_user_comparison(auth_user):
        variant_index = 0
        should_force_variant = True if auth_user and auth_user.company == 'IBM' else False
        return should_force_variant, variant_index


class ExperimentReportTest(TransactionTestCase):

    pass


class VariantTest(TransactionTestCase):

    pass
