import csv
from django.http import HttpResponse

def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'

    writer = csv.writer(response)
    fields = [field.name for field in modeladmin.model._meta.fields]
    writer.writerow(fields)

    for obj in queryset.iterator():
        writer.writerow([str(getattr(obj, field)) for field in fields])

    return response
