from django import template

register = template.Library()


@register.filter(name="get_filter")
def get_filter(d, k):
    return d.get(k, None)
