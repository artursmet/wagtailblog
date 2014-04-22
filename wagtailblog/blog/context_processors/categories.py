from ..models import Category


def categories(request):
    # TODO: Add some caching

    return {'categories_list': Category.objects.all()}
