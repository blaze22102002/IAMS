from django.contrib import admin
from django.http import HttpResponse
import csv
from .models import Asset, Branch, User

class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_id', 'asset_tag', 'employee_id', 'employee_name',
        'group', 'branch', 'status'
    )
    search_fields = ('asset_id', 'asset_tag', 'employee_id', 'serial_number')
    list_filter = ('group', 'branch', 'status')

    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, "Only superusers can export data.", level='error')
            return

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="assets_export.csv"'
        writer = csv.writer(response)

        writer.writerow([
            'asset_id', 'branch_code', 'employee_id', 'employee_name', 'group',
            'business_impact', 'asset_tag', 'description', 'product_name',
            'serial_number', 'remarks', 'status', 'it_poc_remarks'
        ])

        # Use iterator for large datasets
        for asset in queryset.iterator(chunk_size=1000):
            writer.writerow([
                asset.asset_id,
                asset.branch.branch_code if asset.branch else '',
                asset.employee_id,
                asset.employee_name,
                asset.group,
                asset.business_impact,
                asset.asset_tag,
                asset.description,
                asset.product_name,
                asset.serial_number,
                asset.remarks,
                asset.status,
                asset.it_poc_remarks
            ])

        return response

    export_as_csv.short_description = "Export selected assets to CSV"


admin.site.register(Asset, AssetAdmin)
admin.site.register(Branch)
admin.site.register(User)
