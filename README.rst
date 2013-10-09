========================================
Splango: Drop-in Split Testing for Django
========================================

Splango is designed to help you take the first steps with split (A/B)
testing with minimal friction.  It allows you to instantly declare and run a
split test experiment in your templates or in python code, and provides an
admin UI for viewing simple funnel reports on the results.

Template Example
====================

    {% load splangotags %}

    {# first declare the experiment and its variants #}
    {% experiment "signup_text" variants "control,free,trial" %}

    Welcome to my site! Please
    <a href="/signup">

    {# change what is rendered based on which experimental variant you're in #}
    {% hyp "signup_text" "control" %}
       sign up
    {% endhyp %}

    {% hyp "signup_text" "free" %}
       sign up for free
    {% endhyp %}

    {% hyp "signup_text" "trial" %}
       sign up for a trial
    {% endhyp %}
    </a>


Python View Example
====================

    def mypage(request):
        exp_manager = request.experiments_manager

        exp_variant = exp_manager.declare_and_enroll("call_to_action", ["a","b"])

        if exp_variant == "a":
            call_to_action_label = "try it"
        elif exp_variant == "b":
            call_to_action_label = "this might not suck"

        if request.method == "POST":
            form = PleaseDoThisForm(request.POST)

            if form.is_valid():
                exp_manager.log_goal("pleasedoform.completed")
                return HttpResponseRedirect(...)

        else:
            form = PleaseDoThisForm()
            exp_manager.log_goal("pleasedoform.seen")

        return render_to_response("mytemplate.html", { 
           "call_to_action_label": call_to_action_label },
           RequestContext(request))


Things to Note
====================

* In order to filter out bots, Splango injects a javascript fragment into
  your HTTP response. Only clients that have a Django session and can run
  javascript will be tracked in experiments.

* When a user logs in or registers, any experiment enrollments created while
  the user was an anonymous Subject will be merged into a Subject associated
  with the User. In case of conflict, enrollments previously associated with
  a logged-in Subject will override anonymous enrollments. In other words,
  Splango tries to be consistent as to what it presented to a particular
  human, as long as we can identify them.


Installation
====================

* Ensure you have the dependencies:
  * django's session package
  * django's admin for viewing results
  * jQuery

* Put the splango directory somewhere in your PYTHON_PATH.

* In your project's settings.py:

  * add "splango" to INSTALLED_APPS

  * add this to your MIDDLEWARE_CLASSES after the session and auth
    middleware:

        'splango.middleware.ExperimentsMiddleware'

* In your urls.py, include the splango urls and admin_urls modules:

        (r'^splango/', include('splango.urls')),

* Ensure jQuery is available on all text/html responses. Otherwise splango
  will not work. Splango will remind you of this by putting annoying
  javascript alert() messages on such pages if settings.DEBUG is true.

* Finally, go to /splango/admin to create and view experiments.


Usage Notes
====================

* The names of experiments and goals are their sole identifier. This keeps
  things simple, but also means that typos can mess things up.

* Hypotheses within an experiment must have unique names, but you can reuse
  a hypothesis name (e.g. "control") in multiple experiments if you wish.



Other features
====================

* First visit goal (optional)
  Optionally, define a goal to be logged when the first visit to your site
    is made:

        SPLANGO_FIRST_VISIT_GOAL = "firstvisit"

    If this is defined, splango will automatically log the goal "firstvisit"
    as being completed on the user's first request.

* Excluding visitors (optional):
  To exclude visitors you can defined a setting for your exclude comparison method, e.g.:
  settings.py
   SPLANGO_EXCLUDE_USER_COMPARISON='myapp.excludes.exclude_ab_user_comparison'

  myapp.excludes.py:
   def exclude_ab_user_comparison(authenticated_user=None):
    should_exclude = False
    if authenticated_user and authenticated_user.is_admin():
        should_exclude = True
        # Exclude all admin users
        return True
    return should_exclude

  To catch visitors that are excluded (and not enrolled in the experiment) in templates, use:
  {% hyp "sample_experiment" "" %}

  Or in views with:
  if variant.name = "":
     # Handle excluded visitors here

* Force first variant on certain visitors (optional)
 In some cases you may want to expose the same variant to certain group of visitors,
  e.g. all users from the same company should have the same variant (to avoid confusion)

 settings.py:
  SPLANGO_FORCE_FIRST_VARIANT_USER_COMPARISON = 'myapp.comparison.first_variant_users'

 myapp.comparison.py
  def first_variant_users(authenticated_user=None):
    should_force_variant = False
    if authenticated_user and authenticated_user.belongs_to_company('IBM'):
        should_force_variant = True
    return should_force_variant

