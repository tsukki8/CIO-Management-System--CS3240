# AI Citation
# Description: Dashboard and event management views
# AI Use: Generated with GitHub Copilot on 2026-03-29.
#   Prompt: "Build executive and member dashboards with CIO selection, join requests, settings, and event management"
# Notes: Role-based access control, context assembly, CRUD for memberships and events

# AI Citation
# Description: CIO access control and deployment update
# AI Use: Modified with GitHub Copilot on 2026-04-13.
#   Prompt: "Restrict CIO dashboard actions to CIO user types only and update deployment handling for production migrations."
# Notes: Added role-aware checks for CIO detail and event creation flows.

# AI Citation
# Description: Direct messaging feature
# AI Use: Assisted with ChatGPT on 2026-04-13 - modified with GitHub Copilot.
#   Prompt: "Help provide a starting point to implement a basic messaging system in Django."
# Notes: Created DM(Chat) featuer allowing messaging between users to happen.

# AI Citation
# Description: Unread notification feature
# AI Use: Assisted with ChatGPT on 2026-04-28 - modified with GitHub Copilot..
#   Prompt: "Help provide a starting point to add basic unread in-app notifications for new messages in Django."
# Notes: Added notifications for unread messages

# AI Citation
# Description: Landing page view for unauthenticated users
# AI Use: Generated with GitHub Copilot on 2026-04-28.
#   Prompt: "Create a home view that displays site information and contact details for both authenticated and unauthenticated users"
# Notes: Public-facing page with feature overview and CTA buttons

# AI Citation
# Description: Custom logout handler for home-page redirect
# AI Use: Generated with GitHub Copilot on 2026-04-28.
#   Prompt: "Create a logout view that accepts link-based logout and redirects users to the home page"
# Notes: Supports GET-based logout links and sends users back to the public home page

from datetime import datetime
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import CIO, CIORequest, Event, Membership, Profile, Conversation, Message,  Notification

from django.contrib.auth.models import User
from django.db.models import Count, Max


def home_view(request):
    """Public landing page with site information and CTA buttons. Redirects authenticated users to profile."""
    if request.user.is_authenticated:
        return redirect('profiles:profile')
    return render(request, "profiles/home.html")


def logout_view(request):
    """Show a confirmation page on GET and log the user out on POST."""
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("home")

    if request.method == "GET":
        return render(
            request,
            "account/logout.html",
            {
                "logout_action": reverse("profiles:logout"),
                "cancel_url": next_url,
                "redirect_field_name": "next",
                "redirect_field_value": next_url,
            },
        )

    auth_logout(request)
    return redirect('home')


def parse_event_datetime(raw_date):
    """Support both datetime-local and date-only HTML inputs."""
    if not raw_date:
        return None

    try:
        parsed = datetime.fromisoformat(raw_date)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(f"{raw_date}T00:00")
        except ValueError:
            return None

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())

    return timezone.localtime(parsed)


def current_local_datetime_input():
    """Return local datetime string for HTML datetime-local min attribute."""
    return timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M")


def get_user_related_cio_ids(user):
    approved_cio_ids = Membership.objects.filter(
        user=user,
        status="approved",
    ).values_list("cio_id", flat=True)

    owned_cio_ids = CIO.objects.filter(
        created_by=user,
    ).values_list("id", flat=True)

    return set(approved_cio_ids).union(set(owned_cio_ids))


def get_messageable_user_ids(user):
    related_cio_ids = get_user_related_cio_ids(user)
    if not related_cio_ids:
        return set()

    approved_member_ids = Membership.objects.filter(
        cio_id__in=related_cio_ids,
        status="approved",
    ).values_list("user_id", flat=True)

    cio_owner_ids = CIO.objects.filter(
        id__in=related_cio_ids,
    ).values_list("created_by_id", flat=True)

    allowed_ids = set(approved_member_ids).union(set(cio_owner_ids))
    allowed_ids.discard(user.id)
    return allowed_ids


def ensure_upcoming_event_reminders(user, window_hours=24):
    now = timezone.now()
    reminder_window_end = now + timedelta(hours=window_hours)

    upcoming_events = Event.objects.filter(
        attendees=user,
        date__gte=now,
        date__lte=reminder_window_end,
    ).select_related("cio")

    for event in upcoming_events:
        exists = Notification.objects.filter(
            recipient=user,
            event=event,
            notification_type="event_reminder",
        ).exists()

        if not exists:
            Notification.objects.create(
                recipient=user,
                sender=event.host or event.cio.created_by,
                event=event,
                notification_type="event_reminder",
                text=f"Reminder: {event.title} starts on {timezone.localtime(event.date).strftime('%b %d at %I:%M %p')}",
            )


def can_promote_event(cio, days=7, max_promotions=3):
    cutoff = timezone.now() - timedelta(days=days)
    recent_promotions = Event.objects.filter(
        cio=cio,
        promoted_at__gte=cutoff,
    ).count()
    return recent_promotions < max_promotions, max(0, max_promotions - recent_promotions)


def get_dashboard_context(request):
    dashboard = request.GET.get("dashboard")
    if dashboard in {"member", "exec"}:
        return dashboard
    return "exec" if request.user.profile.role == "cio" else "member"


def normalize_event_source(raw_source):
    if raw_source in {"cio", "calendar", "member", "member_promo"}:
        return raw_source
    return "cio"


def with_nav_params(base_url, dashboard_context, source=None):
    params = [f"dashboard={dashboard_context}"]
    if source:
        params.append(f"source={source}")
    return f"{base_url}?{'&'.join(params)}"

@login_required
def profile_view(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    profile = request.user.profile

    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "use_google_image":
            profile.profile_picture = None
            profile.save()
            return redirect(f"{reverse('profiles:profile')}?updated=1")
        
        if action == "upload_profile_picture":
            uploaded_file = request.FILES.get("image_upload")
            if uploaded_file:
                profile.profile_picture.save(uploaded_file.name, uploaded_file)
                profile.save()
            return redirect(f"{reverse('profiles:profile')}?updated=1")
        
    if not profile.role:
        profile.role = "member"
        profile.save(update_fields=["role"])
    
    google_picture_url = None
    google_account = request.user.socialaccount_set.filter(provider="google").first()
    if google_account:
        google_picture_url = google_account.extra_data.get("picture")

    if profile.profile_picture:
        profile_picture_url = profile.profile_picture.url
        has_custom_profile_image = True
    else:
        profile_picture_url = google_picture_url
        has_custom_profile_image = False
    
    return render(
        request,
        "profiles/profile.html",
        {
            "profile": profile,
            "updated": request.GET.get("updated") == "1",
            "profile_picture_url": profile_picture_url,
            "google_picture_url": google_picture_url,
            "has_custom_profile_image": has_custom_profile_image,
        },
    )
def is_user_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin'

@login_required
def user_admin_dashboard(request):
    if not is_user_admin(request.user):
        return redirect("profiles:profile")
    
    users = User.objects.all()
    cio_requests = CIORequest.objects.filter(status="pending").select_related("user").order_by("created_at")

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        new_role = request.POST.get("role")

        target_user = User.objects.filter(id=user_id).first()
        if target_user and target_user.profile.role != "admin" and new_role in ["member", "cio"]:
            target_user.profile.role = new_role
            target_user.profile.save()
    
    return render(request, "profiles/user_admin.html",{
        "users": users,
        "cio_requests": cio_requests,
    })

@login_required
def member_view(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    if request.user.profile.role not in {"member", "cio"}:
        return redirect("profiles:profile")

    query = request.GET.get('q', '')
    cios = CIO.objects.all()
    if query:
        cios = cios.filter(name__icontains=query)

    memberships = Membership.objects.filter(user=request.user)
    membership_map = {m.cio_id: m.status for m in memberships}

    # Source / AI Citation
    # Description: Member dashboard "Owned Clubs" display section
    # Source: Generated with Claude based on analysis of the existing codebase and dashboard structure.
    # AI Use: Generated with Claude during development.
    #   Prompt 1: "Analyze the codebase. I want to implement an Owned Clubs section. How do you think I should approach it?"
    #   Prompt 2: "Make a skeleton for this new feature without changing any existing logic."
    # Notes: Modified to match existing member dashboard logic, ensured owned clubs are excluded from Available CIOs, and preserved all existing behavior.
    owned_clubs = list(CIO.objects.filter(created_by=request.user))
    owned_club_ids = {cio.id for cio in owned_clubs}

    # Source / AI Citation
    # Description: Member dashboard "My Clubs" display section
    # Source: Generated with Claude based on analysis of the existing codebase and dashboard structure.
    # AI Use: Generated with Claude during development.
    #   Prompt 1: "Analyze the codebase. I want to implement a My Clubs section. How do you think I should approach it?"
    #   Prompt 2: "Make a skeleton for this new feature without changing unrelated logic."
    # Notes: Modified to match existing member dashboard logic, template structure, styling, and approved membership behavior.
    approved_memberships = Membership.objects.filter(
        user=request.user, status="approved"
    ).select_related("cio")
    my_clubs = [m.cio for m in approved_memberships]
    my_club_ids = {m.cio_id for m in approved_memberships}
    cios = cios.exclude(id__in=my_club_ids | owned_club_ids)
    cio_request = CIORequest.objects.filter(user=request.user).order_by("-created_at").first()
    ensure_upcoming_event_reminders(request.user)

    promoted_events = Event.objects.filter(
        is_promoted=True,
        date__gte=timezone.now(),
        cio__status="public",
    ).select_related("cio", "host").order_by("date")[:12]

    unread_notifications_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    for cio in cios:
        if cio.created_by_id == request.user.id:
            cio.user_status = "approved"
        else:
            cio.user_status = membership_map.get(cio.id)

    return render(request, "profiles/member.html", {
        'cios': cios,
        'query': query,
        'cio_request': cio_request,
        'promoted_events': promoted_events,
        'unread_notifications_count': unread_notifications_count,
        'my_clubs': my_clubs,
        'owned_clubs': owned_clubs,
    })


@login_required
def request_cio_role(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    if request.user.profile.role != "member":
        return redirect("profiles:profile")

    if request.method == "POST":
        application_text = request.POST.get("application_text", "").strip()
        cio_request, _ = CIORequest.objects.get_or_create(
            user=request.user,
            defaults={"status": "pending", "application_text": application_text},
        )
        if cio_request.status != "approved":
            cio_request.status = "pending"
            cio_request.application_text = application_text
            cio_request.reviewed_at = None
            cio_request.save(update_fields=["status", "application_text", "reviewed_at"])

    cio_request = CIORequest.objects.filter(user=request.user).order_by("-created_at").first()
    return render(request, "profiles/request_cio_role.html", {
        "cio_request": cio_request,
    })


@login_required
def approve_cio_request(request, cio_request_id):
    if request.user.profile.role != 'admin':
        return redirect('profiles:profile')

    if request.method != "POST":
        return redirect("profiles:user_admin_dashboard")

    cio_request = get_object_or_404(CIORequest, id=cio_request_id)
    cio_request.status = "approved"
    cio_request.reviewed_at = timezone.now()
    cio_request.save(update_fields=["status", "reviewed_at"])

    profile = cio_request.user.profile
    profile.role = "cio"
    profile.save(update_fields=["role"])

    return redirect("profiles:user_admin_dashboard")


@login_required
def cio_request_detail(request, cio_request_id):
    if request.user.profile.role != 'admin':
        return redirect('profiles:profile')

    cio_request = get_object_or_404(CIORequest.objects.select_related("user"), id=cio_request_id)
    return render(request, "profiles/cio_request_detail.html", {
        "cio_request": cio_request,
    })


@login_required
def reject_cio_request(request, cio_request_id):
    if request.user.profile.role != 'admin':
        return redirect('profiles:profile')

    if request.method != "POST":
        return redirect("profiles:user_admin_dashboard")

    cio_request = get_object_or_404(CIORequest, id=cio_request_id)
    cio_request.status = "rejected"
    cio_request.reviewed_at = timezone.now()
    cio_request.save(update_fields=["status", "reviewed_at"])

    return redirect("profiles:user_admin_dashboard")

@login_required
def request_join(request, cio_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    if request.user.profile.role not in {"member", "cio"}:
        return redirect("profiles:profile")

    if request.method == "POST":
        membership, _ = Membership.objects.get_or_create(
            user=request.user,
            cio_id=cio_id,
            defaults={"status": "pending"}
        )
        if membership.status == "rejected":
            membership.status = "pending"
            membership.save(update_fields=["status"])

    return redirect('profiles:member')

@login_required
def exec_view(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    if request.user.profile.role != "cio":
        return redirect("profiles:profile")

    cios = CIO.objects.filter(created_by=request.user).order_by("-created_at")
    query = request.GET.get("q", "")
    if query:
        cios = cios.filter(name__icontains=query)

    selected_cio_id = request.GET.get("cio")

    if selected_cio_id:
        cio = cios.filter(pk=selected_cio_id).first()
    else:
        cio = cios.first()

    memberships = (
        Membership.objects.filter(cio__in=cios, status="pending")
        .select_related("user", "cio")
        .order_by("cio__name", "user__username")
    )

    unread_notifications_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    roster = Profile.objects.none()
    last_rsvp_map = {}
    active_cutoff = timezone.now() - timedelta(days=30)

    if cio:
        approved_user_ids = Membership.objects.filter(
            cio=cio,
            status="approved",
        ).values_list("user_id", flat=True)

        roster = (
            Profile.objects.select_related("user")
            .filter(user_id__in=approved_user_ids)
            .order_by("user__last_name", "user__first_name", "user__username")
        )

        last_rsvps = (
            Event.objects.filter(cio=cio, attendees__in=approved_user_ids)
            .values("attendees")
            .annotate(last_rsvp=Max("date"))
        )
        last_rsvp_map = {row["attendees"]: row["last_rsvp"] for row in last_rsvps}

        for member_profile in roster:
            last_rsvp = last_rsvp_map.get(member_profile.user_id)
            member_profile.last_rsvp = last_rsvp
            member_profile.engagement_status = "Active" if last_rsvp and last_rsvp >= active_cutoff else "Inactive"

    can_promote = False
    promotions_left = 0
    if cio:
        can_promote, promotions_left = can_promote_event(cio)


    if cio and cio.profile_picture:
        cio.image_url = cio.profile_picture.url
    elif cio:
        cio.image_url = None
    
    for item in cios:
        if item.profile_picture:
            item.image_url = item.profile_picture.url
        else:
            item.image_url = None

    return render(request, "profiles/exec.html", {
        "cios": cios,
        "cio": cio,
        "query": query,
        "memberships": memberships,
        "roster": roster,
        "cio_image_url": cio.image_url if cio else None,
        "active_cutoff_days": 30,
        "promotions_left": promotions_left,
        "can_promote": can_promote,
        "unread_notifications_count": unread_notifications_count,
    })


@login_required
def cio_calendar_view(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    if request.user.profile.role != "cio":
        return redirect("profiles:profile")

    cios = CIO.objects.filter(created_by=request.user)
    now = timezone.now()

    upcoming_events = Event.objects.filter(
        cio__in=cios,
        date__gte=now,
    ).select_related("cio").order_by("date")

    past_events = Event.objects.filter(
        cio__in=cios,
        date__lt=now,
    ).select_related("cio").order_by("-date")[:20]

    for event in upcoming_events:
        event.calendar_day = event.date.date()

    for event in past_events:
        event.calendar_day = event.date.date()

    dashboard_context = get_dashboard_context(request)

    return render(
        request,
        "profiles/cio_calendar.html",
        {
            "upcoming_events": upcoming_events,
            "past_events": past_events,
            "dashboard_context": dashboard_context,
        },
    )


@login_required
def promote_event_view(request, cio_id, event_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    if request.user.profile.role != "cio":
        return redirect("profiles:profile")

    dashboard_context = get_dashboard_context(request)
    cio_detail_base_url = reverse("profiles:cio_detail", kwargs={"cio_id": cio_id})

    if request.method != "POST":
        return redirect(with_nav_params(cio_detail_base_url, dashboard_context, "cio"))

    cio = get_object_or_404(CIO, id=cio_id, created_by=request.user)
    event = get_object_or_404(Event, id=event_id, cio=cio)

    if event.date <= timezone.now():
        return redirect(f"{with_nav_params(cio_detail_base_url, dashboard_context, 'cio')}&promote=past")

    if cio.status != "public":
        return redirect(f"{with_nav_params(cio_detail_base_url, dashboard_context, 'cio')}&promote=private")

    allowed, _ = can_promote_event(cio)
    if not allowed and not event.is_promoted:
        return redirect(f"{with_nav_params(cio_detail_base_url, dashboard_context, 'cio')}&promote=limit")

    event.is_promoted = True
    event.promoted_at = timezone.now()
    event.save(update_fields=["is_promoted", "promoted_at"])

    return redirect(f"{with_nav_params(cio_detail_base_url, dashboard_context, 'cio')}&promote=ok")

@login_required
def approve_membership(request, membership_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    membership = get_object_or_404(Membership, id=membership_id)

    if membership.cio.created_by != request.user:
        return redirect("profiles:profile")

    if request.method != "POST":
        return redirect("profiles:exec")

    membership.status = "approved"
    membership.save()

    return redirect("profiles:exec")


@login_required
def reject_membership(request, membership_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    membership = get_object_or_404(Membership, id=membership_id)

    if membership.cio.created_by != request.user:
        return redirect("profiles:profile")

    if request.method != "POST":
        return redirect("profiles:exec")

    membership.status = "rejected"
    membership.save()

    return redirect("profiles:exec")

@login_required
def create_cio(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    if request.user.profile.role != "cio":
        return redirect("profiles:exec")

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        CIO.objects.create(
            name=name,
            description=description,
            created_by=request.user,
            status="hidden",
        )
        return redirect("profiles:exec")

    return render(request, "profiles/create_cio.html")

@login_required
def cio_settings_redirect(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    if request.user.profile.role != "cio":
        return redirect("profiles:profile")

    first_cio = CIO.objects.filter(created_by=request.user).order_by("-created_at").first()
    if not first_cio:
        return redirect("profiles:exec")

    return redirect("profiles:cio_settings", cio_id=first_cio.id)


@login_required
def cio_settings_view(request, cio_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    if request.user.profile.role != "cio":
        return redirect("profiles:profile")

    cio = get_object_or_404(CIO, pk=cio_id, created_by=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "delete":
            cio.delete()
            return redirect("profiles:exec")

        if action == "save":
            cio.name = request.POST.get("name", "").strip()
            cio.description = request.POST.get("description", "").strip()
            cio.status = request.POST.get("status", "hidden")

            if not cio.name:
                return render(
                    request,
                    "profiles/cio_settings.html",
                    {
                        "cio": cio,
                        "error": "CIO name is required.",
                    },
                )

            valid_statuses = {"public", "hidden"}
            if cio.status not in valid_statuses:
                cio.status = "hidden"

            uploaded_file = request.FILES.get("image_upload")
            if uploaded_file:
                    cio.profile_picture.save(uploaded_file.name, uploaded_file)

            cio.save()
            return redirect(f"{reverse('profiles:exec')}?cio={cio.id}")

    return render(request, "profiles/cio_settings.html", {"cio": cio})


@login_required
def cio_detail(request, cio_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    cio = get_object_or_404(CIO, id=cio_id)
    dashboard_context = get_dashboard_context(request)
    is_cio_owner = (
        request.user.profile.role == "cio"
        and request.user == cio.created_by
    )

    if not is_cio_owner:
        membership = Membership.objects.filter(
            user=request.user,
            cio=cio,
            status="approved",
        ).first()

        if not membership:
            if dashboard_context == "member":
                return redirect("profiles:member")
            if request.user.profile.role == "cio":
                return redirect("profiles:exec")
            return redirect("profiles:profile")

    now = timezone.now()
    upcoming_events = Event.objects.filter(cio=cio, date__gte=now).order_by("date")
    past_events = Event.objects.filter(cio=cio, date__lt=now).order_by("-date")

    can_promote = False
    promotions_left = 0
    if is_cio_owner:
        can_promote, promotions_left = can_promote_event(cio)

    promote_status = request.GET.get("promote")
    return render(request, "profiles/cio_detail.html", {
        "cio": cio,
        "upcoming_events": upcoming_events,
        "past_events": past_events,
        "total_events": upcoming_events.count() + past_events.count(),
        "can_manage_cio": is_cio_owner,
        "can_promote": can_promote,
        "promotions_left": promotions_left,
        "promote_status": promote_status,
        "dashboard_context": dashboard_context,
    })


@login_required
def create_event(request, cio_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    if request.user.profile.role != "cio":
        return redirect("profiles:profile")

    cio = get_object_or_404(CIO, id=cio_id)

    if cio.created_by != request.user:
        return redirect("profiles:exec")

    dashboard_context = get_dashboard_context(request)
    cio_detail_url = with_nav_params(
        reverse("profiles:cio_detail", kwargs={"cio_id": cio.id}),
        dashboard_context,
        "cio",
    )

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")

        if not title or not date:
            return render(
                request,
                "profiles/create_event.html",
                {
                    "cio": cio,
                    "error": "Title and date are required.",
                    "dashboard_context": dashboard_context,
                },
            )

        event_date = parse_event_datetime(date)
        if not event_date:
            return render(
                request,
                "profiles/create_event.html",
                {
                    "cio": cio,
                    "error": "Please provide a valid date and time.",
                    "min_date_input": current_local_datetime_input(),
                    "dashboard_context": dashboard_context,
                },
            )

        if event_date <= timezone.now():
            return render(
                request,
                "profiles/create_event.html",
                {
                    "cio": cio,
                    "error": "Event date and time must be in the future.",
                    "min_date_input": current_local_datetime_input(),
                    "dashboard_context": dashboard_context,
                },
            )

        Event.objects.create(
            title=title,
            description=description,
            date=event_date,
            cio=cio,
            host=request.user,
        )

        return redirect(cio_detail_url)

    return render(
        request,
        "profiles/create_event.html",
        {
            "cio": cio,
            "min_date_input": current_local_datetime_input(),
            "dashboard_context": dashboard_context,
        },
    )


def user_can_access_cio_events(user, cio):
    """Allow CIO owners and approved members; public CIOs are visible to all logged-in users."""
    if user.profile.role == "cio" and user == cio.created_by:
        return True

    if cio.status == "public":
        return True

    return Membership.objects.filter(
        user=user,
        cio=cio,
        status="approved",
    ).exists()


def redirect_forbidden_cio_access(request):
    dashboard_context = get_dashboard_context(request)
    if dashboard_context == "member":
        return redirect("profiles:member")
    if request.user.profile.role == "cio":
        return redirect("profiles:exec")
    return redirect("profiles:profile")


@login_required
def edit_event(request, cio_id, event_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    if request.user.profile.role != "cio":
        return redirect("profiles:profile")

    cio = get_object_or_404(CIO, id=cio_id)

    if cio.created_by != request.user:
        return redirect("profiles:exec")
    event = get_object_or_404(Event, id=event_id, cio=cio)

    dashboard_context = get_dashboard_context(request)
    cio_detail_url = with_nav_params(
        reverse("profiles:cio_detail", kwargs={"cio_id": cio.id}),
        dashboard_context,
        "cio",
    )

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")

        if not title or not date:
            return render(
                request,
                "profiles/edit_event.html",
                {
                    "cio": cio,
                    "event": event,
                    "error": "Title and date are required.",
                    "dashboard_context": dashboard_context,
                },
            )
        event.host = request.user
        event_date = parse_event_datetime(date)
        if not event_date:
            return render(
                request,
                "profiles/edit_event.html",
                {
                    "cio": cio,
                    "event": event,
                    "error": "Please provide a valid date and time.",
                    "min_date_input": current_local_datetime_input(),
                    "dashboard_context": dashboard_context,
                },
            )
        if event_date <= timezone.now():
            return render(
                request,
                "profiles/edit_event.html",
                {
                    "cio": cio,
                    "event": event,
                    "error": "Event date and time must be in the future.",
                    "min_date_input": current_local_datetime_input(),
                    "dashboard_context": dashboard_context,
                },
            )
        event.title = title
        event.description = description
        event.date = event_date
        event.save()
        return redirect(cio_detail_url)
    return render(
        request,
        "profiles/edit_event.html",
        {
            "cio": cio,
            "event": event,
            "min_date_input": current_local_datetime_input(),
            "dashboard_context": dashboard_context,
        },
    )


@login_required
def event_detail(request, cio_id, event_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    cio = get_object_or_404(CIO, id=cio_id)
    if not user_can_access_cio_events(request.user, cio):
        return redirect_forbidden_cio_access(request)

    event = get_object_or_404(Event, id=event_id, cio=cio)

    is_attending = request.user in event.attendees.all()
    can_manage_event = request.user.profile.role == "cio" and request.user == cio.created_by
    is_past_event = event.date <= timezone.now()
    rsvp_blocked = request.GET.get("rsvp") == "closed"
    dashboard_context = get_dashboard_context(request)
    source = normalize_event_source(request.GET.get("source"))

    if source == "calendar":
        back_url = with_nav_params(reverse("profiles:calendar"), dashboard_context)
        back_label = "Back to Calendar"
    elif source in {"member", "member_promo"}:
        back_url = reverse("profiles:member")
        back_label = "Back to Member Dashboard"
    else:
        back_url = with_nav_params(
            reverse("profiles:cio_detail", kwargs={"cio_id": cio.id}),
            dashboard_context,
            "cio",
        )
        back_label = "Back to CIO"

    rsvp_action_url = with_nav_params(
        reverse("profiles:rsvp_event", kwargs={"cio_id": cio.id, "event_id": event.id}),
        dashboard_context,
        source,
    )

    return render(
        request,
        "profiles/event_detail.html",
        {
            "cio": cio,
            "event": event,
            "is_attending": is_attending,
            "can_manage_event": can_manage_event,
            "is_past_event": is_past_event,
            "rsvp_blocked": rsvp_blocked,
            "dashboard_context": dashboard_context,
            "source": source,
            "back_url": back_url,
            "back_label": back_label,
            "rsvp_action_url": rsvp_action_url,
        },
    )


@login_required
def rsvp_event(request, cio_id, event_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    dashboard_context = request.GET.get("dashboard")
    if dashboard_context not in {"member", "exec"}:
        dashboard_context = "exec" if request.user.profile.role == "cio" else "member"

    source = normalize_event_source(request.GET.get("source"))
    detail_url = with_nav_params(
        reverse("profiles:event_detail", kwargs={"cio_id": cio_id, "event_id": event_id}),
        dashboard_context,
        source,
    )

    if request.method != "POST":
        return redirect(detail_url)

    cio = get_object_or_404(CIO, id=cio_id)
    if not user_can_access_cio_events(request.user, cio):
        return redirect_forbidden_cio_access(request)
    
    event = get_object_or_404(Event, id=event_id, cio_id=cio_id)

    if event.date <= timezone.now():
        connector = "&" if "?" in detail_url else "?"
        return redirect(f"{detail_url}{connector}rsvp=closed")

    if request.user in event.attendees.all():
        event.attendees.remove(request.user)
    else:
        event.attendees.add(request.user)

    return redirect(detail_url)

def get_or_create_conversation(user1, user2):
    conversations = (
        Conversation.objects.annotate(num_users=Count("users"))
        .filter(num_users=2, users=user1)
        .filter(users=user2)
        .distinct()
    )

    if conversations.exists():
        return conversations.first()

    conversation = Conversation.objects.create()
    conversation.users.add(user1, user2)
    return conversation


def get_user_avatar_url(user):
    if hasattr(user, "profile") and user.profile.profile_picture:
        return user.profile.profile_picture.url

    google_account = user.socialaccount_set.filter(provider="google").first()
    if google_account:
        return google_account.extra_data.get("picture")

    return None


def get_relationship_label(current_user, other_user):
   
    user_cio_ids = get_user_related_cio_ids(current_user)
    if not user_cio_ids:
        return None

    owned = CIO.objects.filter(
        id__in=user_cio_ids, created_by=other_user
    ).order_by("name")
    if owned.exists():
        names = ", ".join(c.name for c in owned)
        return f"Your exec · {names}"

    member = CIO.objects.filter(
        id__in=user_cio_ids,
        membership__user=other_user,
        membership__status="approved",
    ).order_by("name").distinct()
    if member.exists():
        names = ", ".join(c.name for c in member)
        return f"Both in: {names}"

    return None


@login_required
def inbox_view(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    allowed_user_ids = get_messageable_user_ids(request.user)
    dashboard_context = get_dashboard_context(request)

    conversations = request.user.conversations.all().prefetch_related("users", "messages").order_by("-created_at")
    filtered_conversations = []
    for conversation in conversations:
        other_user = conversation.users.exclude(id=request.user.id).first()
        if other_user and other_user.id in allowed_user_ids:
            filtered_conversations.append(conversation)

    conversations = filtered_conversations
    selected_conversation_id = request.GET.get("conversation") or request.POST.get("conversation_id")
    selected_new_user_id = request.GET.get("new_user") or request.POST.get("new_user_id")
    selected_conversation = None
    if selected_conversation_id:
        selected_conversation = next((c for c in conversations if str(c.id) == str(selected_conversation_id)), None)

    selected_new_user = None
    if selected_new_user_id:
        selected_new_user = get_object_or_404(User, id=selected_new_user_id)
        if selected_new_user.id == request.user.id or selected_new_user.id not in allowed_user_ids:
            selected_new_user = None

    seen_threads = request.session.get("seen_threads", {})
    if selected_conversation and request.method != "POST":
        selected_last_message = selected_conversation.messages.order_by("-timestamp").first()
        seen_threads[str(selected_conversation.id)] = selected_last_message.timestamp.isoformat() if selected_last_message else ""
        request.session["seen_threads"] = seen_threads

    conversation_summaries = []
    existing_chat_user_ids = set()
    for conversation in conversations:
        other_user = conversation.users.exclude(id=request.user.id).first()
        last_message = conversation.messages.order_by("-timestamp").first()
        if not last_message:
            continue
        seen_at = seen_threads.get(str(conversation.id))
        has_new_reply = bool(
            last_message
            and last_message.sender_id != request.user.id
            and (not seen_at or last_message.timestamp.isoformat() > seen_at)
        )

        if other_user:
            existing_chat_user_ids.add(other_user.id)

        conversation_summaries.append({
            "conversation": conversation,
            "other_user": other_user,
            "last_message": last_message,
            "has_new_reply": has_new_reply,
            "other_user_avatar_url": get_user_avatar_url(other_user) if other_user else None,
        })

    users = User.objects.filter(id__in=allowed_user_ids).exclude(id__in=existing_chat_user_ids)

    new_chat_users = []
    for user in users:
        new_chat_users.append({
            "user": user,
            "avatar_url": get_user_avatar_url(user),
        })
    if not selected_conversation and not selected_new_user:
        selected_conversation = conversations[0] if conversations else None

    selected_other_user = None
    selected_other_user_avatar_url = None
    selected_messages = []
    if selected_conversation:
        selected_other_user = selected_conversation.users.exclude(id=request.user.id).first()
        if selected_conversation:
            Notification.objects.filter(
                recipient=request.user,
                conversation=selected_conversation,
                is_read=False,
        ).update(is_read=True)
        selected_other_user_avatar_url = get_user_avatar_url(selected_other_user) if selected_other_user else None
        selected_messages = selected_conversation.messages.select_related("sender").order_by("timestamp")
        last_message = selected_messages.last()
        seen_threads[str(selected_conversation.id)] = last_message.timestamp.isoformat() if last_message else ""
        request.session["seen_threads"] = seen_threads
    elif selected_new_user:
        selected_other_user = selected_new_user
        selected_other_user_avatar_url = get_user_avatar_url(selected_new_user)

    selected_other_user_relationship = (
        get_relationship_label(request.user, selected_other_user)
        if selected_other_user else None
    )

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if not content:
            return redirect(with_nav_params(reverse("profiles:inbox"), dashboard_context))

        target_conversation = selected_conversation
        if not target_conversation and selected_new_user:
            target_conversation = get_or_create_conversation(request.user, selected_new_user)

        if not target_conversation:
            return redirect(with_nav_params(reverse("profiles:inbox"), dashboard_context))

        recipient = target_conversation.users.exclude(id=request.user.id).first()
        if not recipient or recipient.id not in allowed_user_ids:
            return redirect(with_nav_params(reverse("profiles:inbox"), dashboard_context))

        message = Message.objects.create(
            conversation=target_conversation,
            sender=request.user,
            content=content,
        )

        Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            conversation=target_conversation,
            message=message,
            notification_type="message",
            text=f"{request.user.username} sent you a message",
        )

        return redirect(
            f"{reverse('profiles:inbox')}?dashboard={dashboard_context}&conversation={target_conversation.id}#chat-bottom"
        )

    return render(
        request,
        "profiles/inbox.html",
        {
            "conversation_summaries": conversation_summaries,
            "new_chat_users": new_chat_users,
            "selected_conversation": selected_conversation,
            "selected_other_user": selected_other_user,
            "selected_other_user_avatar_url": selected_other_user_avatar_url,
            "selected_other_user_relationship": selected_other_user_relationship,
            "selected_messages": selected_messages,
            "selected_conversation_id": selected_conversation.id if selected_conversation else None,
            "selected_new_user_id": selected_new_user.id if selected_new_user else None,
            "dashboard_context": dashboard_context,
            "unread_notifications_count": Notification.objects.filter(
                recipient=request.user,
                is_read=False,
            ).count(),
        },
    )


@login_required
def start_chat_view(request, user_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')
    
    other_user = get_object_or_404(User, id=user_id)
    dashboard_context = get_dashboard_context(request)

    if other_user == request.user:
        return redirect(with_nav_params(reverse("profiles:inbox"), dashboard_context))

    allowed_user_ids = get_messageable_user_ids(request.user)
    if other_user.id not in allowed_user_ids:
        return redirect(with_nav_params(reverse("profiles:inbox"), dashboard_context))

    return redirect(f"{reverse('profiles:inbox')}?dashboard={dashboard_context}&new_user={other_user.id}")

@login_required
def notifications_view(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    ensure_upcoming_event_reminders(request.user)

    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related("sender", "conversation", "message", "event")

    dashboard_context = get_dashboard_context(request)

    return render(request, "profiles/notifications.html", {
        "notifications": notifications,
        "dashboard_context": dashboard_context,
    })


@login_required
def open_notification_view(request, notification_id):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    dashboard_context = get_dashboard_context(request)

    if notification.conversation_id:
        return redirect(
            f"{reverse('profiles:inbox')}?dashboard={dashboard_context}&conversation={notification.conversation_id}"
        )

    if notification.event_id:
        source = "member" if dashboard_context == "member" else "cio"
        return redirect(
            with_nav_params(
                reverse(
                    "profiles:event_detail",
                    kwargs={
                        "cio_id": notification.event.cio_id,
                        "event_id": notification.event_id,
                    },
                ),
                dashboard_context,
                source,
            )
        )

    return redirect(with_nav_params(reverse("profiles:notifications"), dashboard_context))


@login_required
def mark_all_notifications_read(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    dashboard_context = get_dashboard_context(request)
    return redirect(with_nav_params(reverse("profiles:notifications"), dashboard_context))

@login_required
def calendar_view(request):
    if request.user.profile.role == 'admin':
        return redirect('profiles:user_admin_dashboard')

    ensure_upcoming_event_reminders(request.user)

    user_events = Event.objects.filter(attendees=request.user).order_by("date")

    for event in user_events:
        event.calendar_day = event.date.date()

    unread_notifications_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    dashboard_context = get_dashboard_context(request)

    return render(request, "profiles/calendar.html", {
        "events": user_events,
        "unread_notifications_count": unread_notifications_count,
        "dashboard_context": dashboard_context,
    })
