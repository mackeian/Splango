# coding: utf-8
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from .models import Enrollment, Experiment, ExperimentReport, Goal, GoalRecord, Variant


@staff_member_required
def experiments_overview(request):
    """Show experiments list."""
    experiments = Experiment.objects.all()
    reports = ExperimentReport.objects.all()
    reports_by_id = dict()

    goals = Goal.objects.all()

    for r in reports:
        reports_by_id.setdefault(r.experiment_id, []).append(r)
    for e in experiments:
        e.reports = reports_by_id.get(e.name, [])

    context = {
        "title": "Experiments",
        "experiments": experiments,
        "goals": goals,
    }

    return render_to_response(
        "splango/experiments_overview.html",
        context,
        RequestContext(request))


@staff_member_required
def experiment_detail(request, exp_name):
    """Show the experiment and its reports."""
    exp = get_object_or_404(Experiment, name=exp_name)
    reports = ExperimentReport.objects.filter(experiment=exp)
    exp.enroll_counts_by_variant = exp.enrollment_set.all().values('variant__name').annotate(Count("id")).order_by()

    return render_to_response(
        "splango/experiment_detail.html",
        {"title": exp.name, "exp": exp, "reports": reports},
        RequestContext(request))


@staff_member_required
def experiment_report(request, report_id):
    """Show the experiment report."""
    # Is really necessary ``exp_name`` as a param? An ExperimentReport already
    # has an experiment as a field.

    report = get_object_or_404(ExperimentReport, id=report_id)
    report_rows = report.generate()

    dictionary = {"title": report.title, "exp": report.experiment,
                  "report": report, "report_rows": report_rows, }
    return render_to_response("splango/experiment_report.html", dictionary,
                              RequestContext(request))


@staff_member_required
def experiment_log(request, exp_name, variant, goal):
    """Show an enrollment, that dentifies which variant a subject is assigned
    to in a given experiment.

    In the response, it returns the experiment itself; the activities, that
    shows what goals reached by the subject, with the given variant, and the
    title, that shows the activity in string format.

    :returns: The experiment log response
    """
    exp = get_object_or_404(Experiment, name=exp_name)
    goal = get_object_or_404(Goal, name=goal)

    enrollments = (
        Enrollment.objects
        .filter(experiment=exp, variant__name=variant, subject__goals=goal)
        .select_related("subject")[:1000]
    )
    # 1000 limit is just there to keep this page sane

    goal_records = (
        GoalRecord.objects
        .filter(goal=goal, subject__in=[e.subject for e in enrollments])
        .select_related("goal", "subject")
    )

    title = "Experiment Log: variant %s, goal %s" % (variant, goal)
    activities = list(enrollments) + list(goal_records)
    activities.sort(key=lambda x: x.created)

    dictionary = {"exp": exp, "activities": activities, "title": title}
    return render_to_response("splango/experiment_log.html", dictionary,
                              RequestContext(request))

@staff_member_required
def goal_report(request, goal_name):
    """Goal results for all the variants.

    :param goal_name: The name of the goal
    :return:
    """
    goal = get_object_or_404(Goal, name=goal_name)

    dictionary = {
        "goal": goal,
    }
    return render_to_response("splango/goal_report.html", dictionary,
                              RequestContext(request))

@staff_member_required
def experiment_goal_report(request, goal_name, exp_name):
    """Goal results for all the variants in a experiment.

    :param request:
    :param exp_name: The name of the experiment
    :param goal_name: The name of the goal
    :return:
    """
    experiment = get_object_or_404(Experiment, name=exp_name)
    goal = get_object_or_404(Goal, name=goal_name)

    variants = experiment.get_variants()

    count = goal.get_records_count_per_variant(experiment)

    # if no count, then data is empty
    if count:
        data = {
            key: (Variant.objects.get(pk=key).name, value[0], value[1])
            for key, value in count.items()
        }
    else:
        data = {}

    ctx = {
        "goal": goal,
        "experiment": experiment,
        "variants": variants,
        "count": count,
        "data": data,
        "title": goal.name,
    }

    return render_to_response("splango/experiment_goal_report.html", ctx,
                              RequestContext(request))
