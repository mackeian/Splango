# coding: utf-8
from django.test import TransactionTestCase

from mock import MagicMock

from splango import RequestExperimentManager
from splango.models import (Variant, Subject)
from splango.tests import create_experiment, create_subject, create_variant


class ExperimentManagerTest(TransactionTestCase):

    fixtures = ['admin_user.json']

    def setUp(self):
        self.variant_names = []
        self.experiment = create_experiment()
        self.variant1 = create_variant(name=u"variant 1",
                                       experiment=self.experiment)
        self.variant_names.append(self.variant1.name)
        self.variant2 = create_variant(name=u"variant 2",
                                       experiment=self.experiment)
        self.variant_names.append(self.variant2.name)

    def test_declare_and_enroll(self):
        """Test splango.RequestExperimentManager.declare_and_enroll."""

        # RequestExperimentManager needs a request as a param.
        # Lets do a mock for the request.
        request = MagicMock()

        # Lets instanciate :class:``splango.RequestExperimentManager`` now.
        exp_man = RequestExperimentManager(request)

        # It is needed a subject, because ``exp_man`` will call
        # :func:``splango.RequestExperimentManager.get_or_create_subject`` method. So,
        # we mock that method in order to have the right returned value.
        subject_ = create_subject()
        exp_man.get_or_create_subject = MagicMock(name="Subject")
        exp_man.get_or_create_subject.return_value = subject_

        # Verify that :func:``splango.RequestExperimentManager.get_or_create_subject``
        # actually gets a :class:`Subject` instance.
        mocked_subject = exp_man.get_or_create_subject()
        self.assertIsInstance(mocked_subject, Subject)

        # Now, call
        # :func:``splango.RequestExperimentManager.declare_and_enroll`` and
        # assert if the returned value is a :class:`Variant` instance.
        variant = exp_man.declare_and_enroll(self.experiment.name,
                                             self.variant_names, )
        self.assertIsInstance(variant, Variant)
