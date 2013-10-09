from django.db.utils import IntegrityError
from django.test import TransactionTestCase

from splango.models import Experiment, Subject, GoalRecord
from splango.tests import (
    create_goal, create_goal_record, create_subject, create_enrollment,
    create_experiment, create_experiment_report, create_variant)


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

    pass


class ExperimentReportTest(TransactionTestCase):

    pass


class VariantTest(TransactionTestCase):

    pass
