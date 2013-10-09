import logging

from .models import Subject, Experiment, Enrollment, GoalRecord, Variant
from .utils import is_first_visit, replace_insensitive


logger = logging.getLogger(__name__)

SPLANGO_SUBJECT = "SPLANGO_SUBJECT"
SPLANGO_QUEUED_UPDATES = "SPLANGO_QUEUED_UPDATES"

# borrowed from debug_toolbar
_HTML_TYPES = ('text/html', 'application/xhtml+xml')


class RequestExperimentManager:

    def __init__(self, request):
        #logger.debug("REM init")
        self.request = request
        self.user_at_init = request.user
        self.queued_actions = []

    def enqueue(self, action, params):
        self.queued_actions.append((action, params))

    def process_from_queue(self, action, params):
        logger.info("dequeued: %s (%s)" % (str(action), repr(params)))

        if action == "enroll":
            exp = Experiment.objects.get(name=params["exp_name"])
            variant = params["variant"]
            exp.get_or_create_enrollment(self.get_subject(), variant)

        elif action == "log_goal":
            goal_record = GoalRecord.record(self.get_subject(),
                                            params["goal_name"],
                                            params["request_info"],
                                            extra=params.get("extra"))
            logger.info("goal! %s" % str(goal_record))

        else:
            raise RuntimeError("Unknown queue action '%s'." % action)

    def finish(self, response):
        """Decide what to do if subject is human or not."""

        current_user = self.request.user

        if self.user_at_init != current_user:
            logger.info("user status changed over request: %s --> %s"
                        % (str(self.user_at_init), str(current_user)))

            if not(current_user.is_authenticated()):
                # User logged out. It's a new session, nothing special.
                pass
            else:
                # User has just logged in (or registered).
                # We'll merge the session's current Subject with
                # an existing Subject for this user, if exists,
                # or simply set the subject.registered_as field.

                old_subject = self.request.session.get(SPLANGO_SUBJECT)

                try:
                    existing_subject = Subject.objects.get(
                        registered_as=current_user)
                    # there is an existing registered subject!
                    if old_subject and old_subject.id != existing_subject.id:
                        # merge old subject's activity into new
                        old_subject.merge_into(existing_subject)

                    # whether we had an old_subject or not, we must
                    # set session to use our existing_subject
                    self.request.session[SPLANGO_SUBJECT] = existing_subject

                except Subject.DoesNotExist:
                    # promote current subject to registered!
                    subject = self.get_subject()
                    subject.registered_as = current_user
                    subject.save()

        for (action, params) in self.queued_actions:
            self.process_from_queue(action, params)
        self.queued_actions = []

        return response

    def get_subject(self):
        sezzion = self.request.session
        subject = sezzion.get(SPLANGO_SUBJECT)
        if not subject:  # TODO: shouldn't this be ``if subject is None``?
            subject = Subject()
            self.request.session[SPLANGO_SUBJECT] = subject
            subject.save()
            logger.info("created subject: %s" % str(subject))
        sub = subject
        return sub

    def declare_and_enroll(self, exp_name, variants, selected_variant=None):
        '''
        declare an experiment, and enroll the user in a variant

        the variant is chosen randomly from variants,
        or if selected_variant is supplied, from selected_variant.
        '''
        exp = Experiment.declare(exp_name, variants)

        subject = self.get_subject()
        selected_variant_obj = None
        if selected_variant:
            selected_variant_obj, created = Variant.objects.get_or_create(
                    name=selected_variant,
                    experiment=exp)

        enrollment = exp.get_or_create_enrollment(subject, variant=selected_variant_obj)
        if enrollment:
            variant = enrollment.variant
        else:
            variant = Variant()
        logger.info("got variant %s for subject %s" %
                    (str(variant), str(subject)))

        return variant

    def log_goal(self, goal_name, extra=None):
        request_info = GoalRecord.extract_request_info(self.request)

        self.enqueue("log_goal", {
            "goal_name": goal_name,
            "request_info": request_info,
            "extra": extra
        })
