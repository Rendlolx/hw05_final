from datetime import datetime


def year(request):
    a = datetime.now()
    a = int(a.strftime('%Y'))
    print(a)
    return {
        'year': a,
    }
