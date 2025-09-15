import random
from django.db.models import Sum, F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import Quote, Source
from .forms import QuoteForm, SourceForm


def _weighted_random_quote():
    qs = Quote.objects.select_related('source').all()
    total = qs.aggregate(s=Sum('weight'))['s'] or 0
    if total <= 0:
        return None
    r = random.randint(1, total)
    acc = 0
    for q in qs:
        acc += q.weight
        if r <= acc:
            return q
    return qs.last() if qs.exists() else None


def random_quote_view(request):
    quote = _weighted_random_quote()
    if quote:
        Quote.objects.filter(pk=quote.pk).update(views=F('views') + 1)
        quote.refresh_from_db(fields=['views'])
    ctx = {'quote': quote}
    return render(request, 'quotes/random.html', ctx)


@require_http_methods(['POST'])
def vote_quote_view(request, pk, action):
    quote = get_object_or_404(Quote, pk=pk)
    if action == 'like':
        Quote.objects.filter(pk=quote.pk).update(likes=F('likes') + 1)
    elif action == 'dislike':
        Quote.objects.filter(pk=quote.pk).update(dislikes=F('dislikes') + 1)
    else:
        messages.error(request, 'Неизвестное действие.')
    return redirect(request.META.get('HTTP_REFERER') or reverse('quotes:random'))


def add_source_view(request):
    if request.method == 'POST':
        form = SourceForm(request.POST)
        if form.is_valid():
            src = form.save()
            messages.success(request, f'Источник "{src.name}" добавлен.')
            return redirect('quotes:add_quote')
    else:
        form = SourceForm()
    return render(request, 'quotes/add_source.html', {'form': form})


def add_quote_view(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save()
            messages.success(request, 'Цитата успешно добавлена.')
            return redirect('quotes:random')
    else:
        form = QuoteForm()
    return render(request, 'quotes/add_quote.html', {
        'form': form,
        'has_sources': Source.objects.exists(),
    })


def top_quotes_view(request):
    # Параметры запроса
    q = (request.GET.get('q') or '').strip()              # поиск по тексту цитаты
    source_query = (request.GET.get('source') or '').strip()  # поиск по имени источника
    sort = (request.GET.get('sort') or 'likes').lower()   # likes|views
    order = (request.GET.get('order') or 'desc').lower()  # asc|desc
    try:
        limit = int(request.GET.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 200))  # защита от крайностей

    base_qs = Quote.objects.select_related('source')

    if q:
        base_qs = base_qs.filter(text__icontains=q)
    if source_query:
        base_qs = base_qs.filter(source__name__icontains=source_query)

    total_count = base_qs.count()

    sort_field = {'likes': 'likes', 'views': 'views'}.get(sort, 'likes')
    prefix = '' if order == 'asc' else '-'
    qs = base_qs.order_by(f'{prefix}{sort_field}', '-weight', '-id')[:limit]

    ctx = {
        'quotes': qs,
        'sources': Source.objects.only('name').order_by('name'),
        'params': {
            'q': q,
            'source': source_query,
            'sort': sort_field,
            'order': 'asc' if order == 'asc' else 'desc',
            'limit': limit,
            'total_count': total_count,
            'current_count': min(limit, total_count),
        },
    }
    return render(request, 'quotes/top.html', ctx)
