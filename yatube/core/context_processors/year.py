import datetime


def year(request):
    now = datetime.datetime.now().year
    """Добавляет переменную с текущим годом."""
    return {"year": now}
