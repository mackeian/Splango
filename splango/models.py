import logging
import random

import caching.base
from django.db import models

from utils import user_model

User = user_model()

logger = logging.getLogger(__name__)

_NAME_LENGTH = 30


class Goal(models.Model):

    """An experiment goal, that is what we are waiting to happen."""

    name = models.CharField(max_length=_NAME_LENGTH, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    def get_records_total(self, experiment):
        """Get the goal records total for an experiment, including all its
        variants

        """
        inner_qs = Enrollment.objects.filter(
            variant__in=experiment.get_variants()).values('subject')

        return GoalRecord.objects.filter(
            goal=self, subject__in=inner_qs).count()

    def get_records_count_per_variant(self, experiment):
        """Get the goal records count and the respective percentage per
        variant.

         >> goal.get_records_count_per_variant(experiment)
         {8: (1, 25.0), 1: (2, 50.0), 2: (0, 0.0), 6: (1, 25.0), 9: (0, 0.0)}

        :param experiment:
        :type experiment: :class:`Experiment`
        :return: count of :class:`GoalRecord` objects and percentage for each
            variant of ``experiment``
        :rtype: dict

        """
        total = self.get_records_total(experiment)

        if total == 0:
            return total

        # get the goal records per variant
        gr_per_variant = {}

        # for each variant, associates the count and the percentage
        for v in experiment.get_variants():
            gr_count_variant = v.get_goal_records(self).count()
            if total > 0:
                gr_percentage = (gr_count_variant * 100.0) / total
            else:
                gr_percentage = 0
            gr_per_variant[v.pk] = (gr_count_variant, gr_percentage)

        return gr_per_variant


class Subject(models.Model):

    """An experimental subject, possibly also a registered user (at creation
    or later on."""

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    registered_as = models.ForeignKey(User, null=True, editable=False,
                                      unique=True)
    goals = models.ManyToManyField(Goal, through='GoalRecord')

    def __unicode__(self):
        if self.registered_as:
            prefix = "registered"
        else:
            prefix = "anonymous"

        return u"%s subject #%d" % (prefix, self.id)

    def merge_into(self, other_subject):
        """Move the enrollments and goal records associated with this subject
        into ``other_subject``, preserving ``other_subject``'s
        enrollments in case of conflict.

        """
        other_goals = dict(((g.name, 1) for g in other_subject.goals.all()))

        for goal_record in self.goalrecord_set.all().select_related("goal"):
            if goal_record.goal.name not in other_goals:
                goal_record.subject = other_subject
                goal_record.save()
            else:
                goal_record.delete()

        other_exps = dict(((e.experiment_id, 1)
                           for e in other_subject.enrollment_set.all()))

        for e in self.enrollment_set.all():
            if e.experiment_id not in other_exps:
                e.subject = other_subject
                e.save()
            else:
                e.delete()

        self.delete()

    def is_registered_user(self):
        """Is this subject associated to a registered user?

        :return: True if subject is a registered user i.e. associated to a
          :class:`django.contrib.auth.models.User`
        :rtype: bool

        """
        return self.registered_as is not None
    is_registered_user.boolean = True

    def get_variants(self):
        """Return all the variants shown to this subject.

        The relationship is established through :class:`Enrollment`, which
        has foreign keys to both :class:`Variant` and :class:`Subject`.

        .. seealso::
            See analogous method :meth:`Variant.get_subjects`.

        :return: the variants
        :rtype: queryset of :class:`Variant`

        """
        return Enrollment.objects.filter(subject=self).values('variant')


class GoalRecord(models.Model):

    """Associate the goal reached by a subject with that subject."""

    goal = models.ForeignKey(Goal)
    subject = models.ForeignKey(Subject)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    req_HTTP_REFERER = models.CharField(max_length=255, blank=True)
    req_REMOTE_ADDR = models.IPAddressField(blank=True)
    req_path = models.CharField(max_length=255, blank=True)

    extra = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (('subject', 'goal'),)
        # never record the same goal twice for a given subject

    @staticmethod
    def extract_request_info(request):
        return dict(
            req_HTTP_REFERER=request.META.get("HTTP_REFERER", "")[:255],
            req_REMOTE_ADDR=request.META["REMOTE_ADDR"],
            req_path=request.path[:255])

    @classmethod
    def record(cls, subject, goal_name, request_info, extra=None):
        logger.warn("goal_record %r" %
                    [subject, goal_name, request_info, extra])
        goal, created = Goal.objects.get_or_create(name=goal_name)
        goal_record, created = cls.objects.get_or_create(
            subject=subject, goal=goal, defaults=request_info)

        if not created and not goal_record.extra and extra:
            # add my extra info to the existing goal record
            goal_record.extra = extra
            goal_record.save()

        return goal_record

    @classmethod
    def record_user_goal(cls, user, goal_name):
        subject, created = Subject.objects.get_or_create(registered_as=user)
        cls.record(subject, goal_name, {})

    def __unicode__(self):
        return u"%s by subject #%d" % (self.goal, self.subject_id)


class Enrollment(caching.base.CachingMixin, models.Model):

    """Identifies which variant a subject is assigned to in a given
    experiment."""

    subject = models.ForeignKey('splango.Subject', editable=False)
    # TODO: remove experiment because it is already present in variant
    # Note: For now, we will keep experiment as a field in Enrollment, even
    # knowing that it produces an denormalized database structure.
    # Experiment present as a field is required to get a unique subject in only
    # one experiment, as declared at line 205
    experiment = models.ForeignKey('splango.Experiment', editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    variant = models.ForeignKey('splango.Variant')

    objects = caching.base.CachingManager()

    class Meta:
        unique_together = (('subject', 'experiment'),)

    def __unicode__(self):
        return (u"experiment '%s' subject #%d -- variant %s" %
                (self.experiment.name, self.subject_id, self.variant))


class Experiment(caching.base.CachingMixin, models.Model):

    """A named experiment.

    An experiment has a lot of variants, and a variant belongs to only one
    experiment.

    """

    name = models.CharField(max_length=_NAME_LENGTH, primary_key=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = caching.base.CachingManager()

    # moved to variant, variant has the experiment
    # subjects = models.ManyToManyField(Subject, through=Enrollment)

    def __unicode__(self):
        return self.name

    # def set_variants(self, variant_list):
    #     self.variants = "\n".join(variant_list)

    def get_variants(self):
        return self.variants.all()

    def get_random_variant(self):
        """Return one of the object's variants chosen in a random way.

        .. warning::
            There is a reason why a :class:`random.Random` generator is created
            in every call: using :func:`random.choice` used use the same
            generator every time because of it is not really a function but
            a method of a hidden instance of :class:`random.Random`, defined in
            :mod:`random`. Debugging we could see that the instance's internal
            state was always the same, thus the output will not be random!

            Also, :meth:`random.Random.jumpahead` seemed to be the solution
            but it is not recommended and was removed in Python 3.

        :return: variant
        :rtype: basestring

        """
        generator = random.Random()
        return generator.choice(self.get_variants())

    def variants_commasep(self):
        variants = self.get_variants()
        variants_names = [v.name for v in variants]
        return ','.join(variants_names)

    def get_or_create_enrollment(self, subject, variant=None):
        """Get or create an :class:`Enrollment` object for ``subject``.

        Only if the object is to be created will ``variant`` be used.
        If ``variant`` is None, a random variant will be assigned.

        :param subject: the subject of the enrollment
        :type subject: :class:`Subject`
        :param variant: when creating the object, it is the variant to use;
            if None, a random variant will be used
            created, this will be the value for :attr:`Enrollment.variant`
        :type variant: str or None
        :return: the enrollment for ``subject``
        :rtype: :class:`Enrollment`

        """
        if variant is None:
            variant = self.get_random_variant()
        enrollment, created = Enrollment.objects.get_or_create(
            subject=subject,
            experiment=self,
            defaults={"variant": variant}
        )
        return enrollment

    @classmethod
    def declare(cls, name, variants_names):
        """create or update an experiment and its variants (variant names
        given).

        """
        obj, created = cls.objects.get_or_create(name=name)

        for v in variants_names:
            Variant.objects.get_or_create(name=v, experiment=obj)
        return obj


class ExperimentReport(models.Model):

    """A report on the results of an experiment."""

    experiment = models.ForeignKey(Experiment)
    title = models.CharField(max_length=100, blank=True)
    funnel = models.TextField(
        help_text="List the goals, in order and one per line, that "
                  "constitute this report's funnel.")

    def __unicode__(self):
        return u"%s - %s" % (self.title, self.experiment.name)

    def get_funnel_goals(self):
        return [x.strip() for x in self.funnel.split("\n") if x]

    def generate(self):
        """Generate the report for experiment.

        Generate the report of a experiment goals and variants.

        Associate each variant with a goal, and associate the variant
        count too.

        :returns: A dict with goals, variants and variants counts associated
          to each goal

        """
        result = []
        exp = self.experiment
        variants = self.experiment.get_variants()
        goals = self.get_funnel_goals()

        # count initial participation
        variant_counts = []

        for v in variants:
            # variant_counts.append(exp.subjectvariant_set.filter(variant=v).\
            #     aggregate(ct=Count("variant")).get("ct",0))
            val = Enrollment.objects.filter(experiment=exp, variant=v).count()
            variant_counts.append(dict(
                val=val,
                variant_name=v,
                pct=None,
                pct_cumulative=1,
                pct_cumulative_round=100))

        result.append({"goal": None,
                       "variant_names": variants,
                       "variant_counts": variant_counts})

        for previ, goal in enumerate(goals):
            try:
                goal = Goal.objects.get(name=goal)
            except Goal.DoesNotExist:
                logger.warn("No such goal <<%s>>." % goal)
                goal = None

            variant_counts = []

            for vi, v in enumerate(variants):
                if goal:
                    vcount = Enrollment.objects.filter(
                        experiment=exp, variant=v, subject__goals=goal).count()
                    prev_count = result[previ]["variant_counts"][vi]["val"]

                    if prev_count == 0:
                        pct = 0
                    else:
                        pct = float(vcount) / float(prev_count)

                else:
                    vcount = 0
                    pct = 0

                pct_cumulative = \
                    pct * result[previ]["variant_counts"][vi]["pct_cumulative"]

                variant_counts.append(dict(
                    val=vcount,
                    variant_name=variants[vi],
                    pct=pct,
                    pct_round=("%0.2f" % (100 * pct)),
                    pct_cumulative=pct_cumulative,
                    pct_cumulative_round=("%0.2f" % (100 * pct_cumulative)), ))

            result.append({"goal": goal, "variant_counts": variant_counts})

        return result


class Variant(caching.base.CachingMixin, models.Model):

    """An Experiment Variant, with optional weight

    (The weight is not considered at the moment)

    """

    experiment = models.ForeignKey('splango.Experiment',
                                   related_name="variants")

    name = models.CharField(max_length=_NAME_LENGTH, blank=True)
    objects = caching.base.CachingManager()
    # weight = models.IntegerField(null=True, blank=True,
    #                              help_text="The priority of the variant")

    def __unicode__(self):
        # TODO: check that variant calls are correct
        # Due to the `Variant` change from string to class, almost every
        # part of this project is working with `variant` as a string.
        # In order to continue working like that, ``__unicode__`` is returning
        # ``self.name`` now.
        return self.name

    def get_subjects(self):
        """Return all the subjects to whom this variant was shown.

        The relationship is established through :class:`Enrollment`, which
        has foreign keys to both :class:`Variant` and :class:`Subject`.

        .. seealso::
            See analogous method :meth:`Subject.get_variants`.

        :return: the subjects
        :rtype: queryset of :class:`Subject`

        """
        return Enrollment.objects.filter(variant=self).values('subject')

    def get_goal_records(self, goal):
        """Return all the records of ``goal`` for this variant.

        :param goal:
        :type goal: :class:`Goal`
        :return: the goal records
        :rtype: queryset of :class:`GoalRecord`

        """
        subjects = self.get_subjects()
        return GoalRecord.objects.filter(goal=goal, subject__in=subjects)
