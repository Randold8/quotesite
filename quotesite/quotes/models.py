# quotes/models.py
from urllib.parse import urlparse
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone

class Source(models.Model):
    TYPE_CHOICES = (
        ('movie', 'Фильм'),
        ('book', 'Книга'),
        ('other', 'Другое'),
    )
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default='other')
    image_url = models.URLField('Ссылка на изображение (постер/обложка)', max_length=500, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        if self.image_url:
            self.image_url = self.image_url.strip()
            p = urlparse(self.image_url)
            if p.scheme not in ('http', 'https'):
                raise ValidationError({'image_url': 'URL должен начинаться с http:// или https://'})
        return super().clean()

    def __str__(self):
        return f'{self.get_type_display()}: {self.name}'


class Quote(models.Model):
    text = models.TextField()
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='quotes')
    weight = models.PositiveIntegerField(default=1)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0, db_index=True)  # <-- новое поле
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-likes', '-created_at']

    def clean(self):
        if self.text:
            self.text = self.text.strip()

        dup_qs = Quote.objects.filter(text__iexact=self.text)
        if self.pk:
            dup_qs = dup_qs.exclude(pk=self.pk)
        if dup_qs.exists():
            raise ValidationError({'text': 'Такая цитата уже существует (дубликат).'})

        if self.source_id:
            count_qs = Quote.objects.filter(source_id=self.source_id)
            if self.pk:
                count_qs = count_qs.exclude(pk=self.pk)
            if count_qs.count() >= 3:
                raise ValidationError({'source': 'У этого источника уже есть 3 цитаты. Удалите/измените существующие.'})

        if self.weight < 1:
            raise ValidationError({'weight': 'Вес должен быть целым числом >= 1.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'[{self.source}] {self.text[:60]}...'


class PageStat(models.Model):
    key = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.key}: {self.count}'

    @classmethod
    def bump(cls, key='home'):
        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(key=key)
            obj.count = F('count') + 1
            obj.save(update_fields=['count'])
            obj.refresh_from_db(fields=['count'])
            return obj.count
