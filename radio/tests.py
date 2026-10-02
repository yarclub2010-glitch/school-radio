import datetime
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import BreakSlot, Track

MEDIA = tempfile.mkdtemp()


def mp3(name='song.mp3'):
    return SimpleUploadedFile(name, b'ID3fake-audio', content_type='audio/mpeg')


@override_settings(MEDIA_ROOT=MEDIA)
class RadioTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def upload(self, **extra):
        data = {'title': 'Группа крови', 'artist': 'Кино', 'uploaded_by': 'Петя', 'school_class': '9б', 'file': mp3()}
        data.update(extra)
        return self.client.post(reverse('upload'), data)

    def test_upload_goes_to_moderation(self):
        self.assertRedirects(self.upload(), reverse('playlist'))
        track = Track.objects.get()
        self.assertEqual(track.status, Track.Status.PENDING)
        self.assertEqual(track.school_class, '9Б')
        self.assertNotContains(self.client.get(reverse('playlist')), 'Группа крови')

    def test_rejects_non_audio(self):
        resp = self.upload(file=SimpleUploadedFile('virus.exe', b'MZ'))
        self.assertContains(resp, 'Подходят только файлы')
        self.assertFalse(Track.objects.exists())

    def test_moderation_requires_staff(self):
        self.assertEqual(self.client.get(reverse('moderation')).status_code, 302)

    def test_approve_shows_in_playlist_and_hall(self):
        self.upload()
        staff = User.objects.create_user('teacher', password='x', is_staff=True)
        self.client.force_login(staff)
        track = Track.objects.get()
        self.client.post(reverse('moderation'), {'track': track.id, 'action': 'approve'})
        self.assertContains(self.client.get(reverse('playlist')), 'Группа крови')
        data = self.client.get(reverse('hall_data')).json()
        self.assertEqual([t['id'] for t in data['tracks']], [track.id])

    def test_played_counts_and_now_playing(self):
        track = Track.objects.create(title='A', artist='B', file=mp3(), uploaded_by='x', school_class='5А',
                                     status=Track.Status.APPROVED)
        self.client.post(reverse('hall_played', args=[track.id]))
        track.refresh_from_db()
        self.assertEqual(track.plays, 1)
        self.assertContains(self.client.get(reverse('playlist')), 'Сейчас в актовом зале')

    def test_schedule_filters_weekdays(self):
        BreakSlot.objects.create(name='Будни', start=datetime.time(10), end=datetime.time(10, 15))
        BreakSlot.objects.create(name='Суббота', start=datetime.time(11), end=datetime.time(11, 15), weekdays='5')
        monday = datetime.date(2026, 9, 28)
        self.assertEqual([b.name for b in BreakSlot.schedule_for(monday)], ['Будни'])
