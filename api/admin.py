from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Client, Automation, Workflow, Message, Log, Guide, GuideSection, GuideStep, GuideProgress, Feature, Plan, PlanFeature, ClientFeatureOverride, PlanAuditLog

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'status', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'status', 'client')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'status', 'client')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Client)
admin.site.register(Automation)
admin.site.register(Workflow)
admin.site.register(Message)
admin.site.register(Log)

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'category', 'status', 'estimated_time', 'order')
    list_filter = ('category', 'status', 'language')
    search_fields = ('title', 'slug', 'description')

@admin.register(GuideSection)
class GuideSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'guide', 'order')
    list_filter = ('guide',)

@admin.register(GuideStep)
class GuideStepAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'step_type', 'order')
    list_filter = ('step_type', 'section__guide')

admin.site.register(GuideProgress)

# Register new entitlement models
admin.site.register(Feature)
admin.site.register(Plan)
admin.site.register(PlanFeature)
admin.site.register(ClientFeatureOverride)
admin.site.register(PlanAuditLog)

