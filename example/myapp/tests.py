# -*- coding: utf-8 -*-
from unittest import TestCase

from mock import MagicMock
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from django.conf import settings
from django.contrib.auth import load_backend
import django.contrib.auth.models as auth_models
from django.test import LiveServerTestCase
from django.utils.importlib import import_module

from splango import RequestExperimentManager
from splango.models import (Experiment, Variant, Subject, Enrollment)
from splango.tests import create_experiment, create_subject, create_variant


class InitTest(TestCase):
    """Tests for functions in splango.__init__
    """
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


class BehaviourTest(LiveServerTestCase):
    """Functional tests for splango."""
    fixtures = ['admin_user.json']

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)
        self.test_username = 'selenium-test'
        self.test_password = 'spam'
        self.test_user = auth_models.User.objects.create_user(
            username=self.test_username, password=self.test_password)

        self.test_user.is_staff = True
        self.test_user.save()

    def tearDown(self):
        self.browser.quit()

    def _goto(self, relative_url):
        return self.browser.get(self.live_server_url + relative_url)

    def _login(self, username='admin', pwd='admin'):
        # Jenny opens the admin login page in browser
        self.browser.get(self.live_server_url + '/admin/')

        # She sees the familiar 'Django administration' heading
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('Django administration', body.text)

        # She types in her username and passwords and hits return
        username_field = self.browser.find_element_by_name('username')
        username_field.send_keys(username)
        password_field = self.browser.find_element_by_name('password')
        password_field.send_keys(pwd)
        password_field.send_keys(Keys.RETURN)

    def get_user(self):
        """Return the user corresponding to the current session in the web
        client, either a logged-in 'regular' user or anonymous.

        :return: the user which is assigned to the current session
        :rtype: :class:`auth_models.User` or :class:`auth_models.AnonymousUser`


        Implementation based on: :func:`django.contrib.auth.get_user`

        """
        SESSION_KEY = '_auth_user_id'
        BACKEND_SESSION_KEY = '_auth_user_backend'

        try:
            session = self.get_session()
            user_id = session[SESSION_KEY]
            backend_path = session[BACKEND_SESSION_KEY]
            backend = load_backend(backend_path)
            user = backend.get_user(user_id) or auth_models.AnonymousUser()
        except KeyError:
            user = auth_models.AnonymousUser()
        return user

    def get_session(self):
        """Return the stored session corresponding to this web client
        (:attr:`driver`, instance of :class:`WebDriver`) as a dictionary, with
        the data already decoded. The session key is in a cookie stored in the
        web client.

        :return: a session dictionary
        :rtype: :class:`dict`

        Implementation based on:
        :meth: `django.contrib.sessions.middleware.SessionMiddleware.process_request`

        """
        cookie_value_key = u'value'
        engine = import_module(settings.SESSION_ENGINE)
        cookie_name = settings.SESSION_COOKIE_NAME

        session_cookie = self.browser.get_cookie(cookie_name)
        session_key = session_cookie.get(cookie_value_key)
        store = engine.SessionStore(session_key)
        return store.load()

    def test_can_open_admin_login(self):
        # login as admin
        self._login()

        # Jenny's username and password are accepted, and she is taken to
        # the Site Administration page
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('Site administration', body.text)

    def test_as_anonymous_user(self):
        # Jenny goes anonymously to /example/sample/, where is located our
        # example, that shows "Red" or "Blue!"
        self._goto('/example/sample/')

        # Assert that she is still an anon user.
        self.assertIsInstance(self.get_user(), auth_models.AnonymousUser)

        # She should see one of our two variants
        element = self.browser.find_element_by_id('sample_text')
        self.assertTrue(element.text == 'Blue!' or element.text == 'Red')

    def test_generate_many_enrollments(self):
        # test as admin
        self._login()
        self._goto('/example/sample/')
        self.assertEquals(Enrollment.objects.count(), 1)
        self._goto('/admin/logout/')

        # test as selenium-test
        self._login(self.test_username, self.test_password)
        self._goto('/example/sample/')
        self.assertEquals(Enrollment.objects.count(), 2)
        self._goto('/admin/logout/')

        # test without login
        self._goto('/example/sample/')
        self.assertEquals(Enrollment.objects.count(), 3)
        anonymous_enrollment = Enrollment.objects.all()[2]

        # Three enrollments counted. Lets verify that.
        count = Enrollment.objects.count()
        self.assertEquals(count, 3)

        # The last one was an anonymous subject, right?
        self.assertIn("anonymous subject",
                      anonymous_enrollment.subject.__unicode__())

    def test_as_anonymous_user_and_then_as_registered_user(self):
        """Test that an anonymous user is merged into the registered one,
        if he keeps the same session.

        """
        self._goto('/example/sample/')

        # Just one enrollment created
        self.assertEquals(Enrollment.objects.count(), 1)

        # this is an anonymous enrollment
        anonymous_enrollment = Enrollment.objects.all()[0]

        # assert the subject is actually anonymous
        self.assertIn("anonymous subject",
                      anonymous_enrollment.subject.__unicode__())

        # Now login
        self._login()

        # Go to the experiment again
        self._goto('/example/sample/')

        # There is only one enrollment
        self.assertEquals(Enrollment.objects.count(), 1)

        # That enrollment is the same that the previous anonymous enrollment
        # i.e., the anonymous enrollment now is a registered user one.
        not_anon_enrollment = Enrollment.objects.all()[0]
        self.assertEquals(not_anon_enrollment.variant,
                          anonymous_enrollment.variant)

        self.assertEquals(not_anon_enrollment.subject,
                          anonymous_enrollment.subject)
