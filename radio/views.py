from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ModerationForm, TrackUploadForm
from .models import BreakSlot, Track

NOW_PLAYING_KEY = 'hall-now-playing'


def playlist(request):
    tracks = Track.objects.filter(status=Track.Status.APPROVED)
    q = request.GET.get('q', '').strip()
    if q:
        tracks = tracks.filter(Q(title__icontains=q) | Q(artist__icontains=q))
    return render(request, 'radio/playlist.html', {
        'tracks': tracks,
        'q': q,
        'now_playing': cache.get(NOW_PLAYING_KEY),
        'pending_count': Track.objects.filter(status=Track.Status.PENDING).count(),
    })


def upload(request):
    form = TrackUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        track = form.save()
        messages.success(request, f'«{track}» отправлен на проверку. После одобрения он появится в плейлисте.')
        return redirect('playlist')
    return render(request, 'radio/upload.html', {'form': form})


def hall(request):
    return render(request, 'radio/hall.html')


def hall_data(request):
    tracks = Track.objects.filter(status=Track.Status.APPROVED)
    schedule = BreakSlot.schedule_for()
    return JsonResponse({
        'server_time': timezone.localtime().strftime('%H:%M:%S'),
        'tracks': [
            {'id': t.id, 'title': t.title, 'artist': t.artist, 'url': t.file.url,
             'by': f'{t.uploaded_by}, {t.school_class}'}
            for t in tracks
        ],
        'schedule': [
            {'name': b.name, 'start': b.start.strftime('%H:%M:%S'), 'end': b.end.strftime('%H:%M:%S')}
            for b in schedule
        ],
    })


@require_POST
def hall_played(request, pk):
    track = get_object_or_404(Track, pk=pk, status=Track.Status.APPROVED)
    Track.objects.filter(pk=pk).update(plays=F('plays') + 1)
    cache.set(NOW_PLAYING_KEY, str(track), timeout=15 * 60)
    return JsonResponse({'ok': True})


@require_POST
def hall_stopped(request):
    cache.delete(NOW_PLAYING_KEY)
    return JsonResponse({'ok': True})


@staff_member_required
def moderation(request):
    if request.method == 'POST':
        form = ModerationForm(request.POST)
        track = get_object_or_404(Track, pk=request.POST.get('track'))
        if form.is_valid():
            if form.cleaned_data['action'] == 'approve':
                track.status = Track.Status.APPROVED
                messages.success(request, f'«{track}» одобрен.')
            else:
                track.status = Track.Status.REJECTED
                track.reject_reason = form.cleaned_data['reason']
                messages.info(request, f'«{track}» отклонён.')
            track.save()
        return redirect('moderation')
    return render(request, 'radio/moderation.html', {
        'pending': Track.objects.filter(status=Track.Status.PENDING).order_by('created_at'),
    })
