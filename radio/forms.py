from pathlib import Path

from django import forms
from django.conf import settings

from .models import Track

ALLOWED_EXT = {'.mp3', '.ogg', '.m4a', '.wav'}


class TrackUploadForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = ['title', 'artist', 'file', 'uploaded_by', 'school_class']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Например: Звезда по имени Солнце'}),
            'artist': forms.TextInput(attrs={'placeholder': 'Например: Кино'}),
            'uploaded_by': forms.TextInput(attrs={'placeholder': 'Имя и фамилия'}),
            'school_class': forms.TextInput(attrs={'placeholder': '9Б'}),
            'file': forms.ClearableFileInput(attrs={'accept': ','.join(sorted(ALLOWED_EXT))}),
        }
        labels = {'uploaded_by': 'Ваше имя'}

    def clean_file(self):
        f = self.cleaned_data['file']
        if Path(f.name).suffix.lower() not in ALLOWED_EXT:
            raise forms.ValidationError('Подходят только файлы MP3, OGG, M4A или WAV.')
        if f.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(f'Файл больше {settings.MAX_UPLOAD_MB} МБ.')
        return f

    def clean_school_class(self):
        return self.cleaned_data['school_class'].strip().upper()


class ModerationForm(forms.Form):
    action = forms.ChoiceField(choices=[('approve', 'approve'), ('reject', 'reject')])
    reason = forms.CharField(max_length=200, required=False)
