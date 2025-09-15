from django.contrib import admin, messages
from django.utils.html import format_html
from django import forms
from django.db import models

from .models import Source, Quote, PageStat


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'image_thumb', 'name', 'type')
    search_fields = ('name',)
    list_filter = ('type',)

    def image_thumb(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="height:36px;border-radius:6px;">', obj.image_url)
        return '—'
    image_thumb.short_description = 'Обложка'


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'source', 'weight', 'likes', 'dislikes', 'views', 'created_at')
    list_display_links = ('short_text',)
    list_editable = ('weight',)
    list_filter = ('source', 'source__type')
    search_fields = ('text', 'source__name')
    date_hierarchy = 'created_at'
    list_per_page = 25

    readonly_fields = ('created_at',)
    autocomplete_fields = ('source',)
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 6})},
    }
    fieldsets = (
        ('Цитата', {'fields': ('text', 'source')}),
        ('Параметры и статистика', {'fields': ('weight', ('likes', 'dislikes', 'views'))}),
        ('Служебное', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    actions = ['reset_likes', 'reset_dislikes', 'reset_votes']

    @admin.action(description='Сбросить лайки (у выбранных)')
    def reset_likes(self, request, queryset):
        updated = queryset.update(likes=0)
        self.message_user(request, f'Лайки обнулены у {updated} цитат.', level=messages.SUCCESS)

    @admin.action(description='Сбросить дизлайки (у выбранных)')
    def reset_dislikes(self, request, queryset):
        updated = queryset.update(dislikes=0)
        self.message_user(request, f'Дизлайки обнулены у {updated} цитат.', level=messages.SUCCESS)

    @admin.action(description='Сбросить лайки и дизлайки (у выбранных)')
    def reset_votes(self, request, queryset):
        updated = queryset.update(likes=0, dislikes=0)
        self.message_user(request, f'Лайки и дизлайки обнулены у {updated} цитат.', level=messages.SUCCESS)

    def short_text(self, obj):
        return (obj.text[:80] + '...') if obj.text and len(obj.text) > 80 else obj.text
    short_text.short_description = 'Текст'


@admin.register(PageStat)
class PageStatAdmin(admin.ModelAdmin):
    list_display = ('key', 'count')
