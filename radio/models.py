from django.db import models
from django.utils import timezone


class Track(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'На проверке'
        APPROVED = 'approved', 'Одобрен'
        REJECTED = 'rejected', 'Отклонён'

    title = models.CharField('Название', max_length=200)
    artist = models.CharField('Исполнитель', max_length=200)
    file = models.FileField('Файл', upload_to='tracks/%Y/%m/')
    uploaded_by = models.CharField('Кто загрузил', max_length=100)
    school_class = models.CharField('Класс', max_length=10)
    status = models.CharField('Статус', max_length=10, choices=Status.choices, default=Status.PENDING)
    reject_reason = models.CharField('Причина отказа', max_length=200, blank=True)
    plays = models.PositiveIntegerField('Прослушиваний в зале', default=0)
    created_at = models.DateTimeField('Загружен', auto_now_add=True)

    class Meta:
        verbose_name = 'Трек'
        verbose_name_plural = 'Треки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.artist} — {self.title}'


class BreakSlot(models.Model):
    """Перемена: в это время музыка в актовом зале играет, в остальное — молчит."""

    name = models.CharField('Название', max_length=50, help_text='Например: «После 2 урока»')
    start = models.TimeField('Начало')
    end = models.TimeField('Конец')
    weekdays = models.CharField('Дни недели', max_length=20, default='0,1,2,3,4',
                                help_text='Номера дней через запятую: 0 — Пн … 6 — Вс')

    class Meta:
        verbose_name = 'Перемена'
        verbose_name_plural = 'Расписание перемен'
        ordering = ['start']

    def __str__(self):
        return f'{self.name} ({self.start:%H:%M}–{self.end:%H:%M})'

    def days(self):
        return {int(d) for d in self.weekdays.split(',') if d.strip().isdigit()}

    @classmethod
    def schedule_for(cls, day=None):
        day = day or timezone.localdate()
        return [b for b in cls.objects.all() if day.weekday() in b.days()]
