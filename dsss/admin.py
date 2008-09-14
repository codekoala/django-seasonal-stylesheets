from django.contrib import admin
from dsss.models import SeasonalStylesheet, Color, Season, SeasonColor

class ColorInline(admin.TabularInline):
    model = Color

class StylesheetAdmin(admin.ModelAdmin):
    model = SeasonalStylesheet
    list_display = ('name', 'template_name')
    inlines = [ColorInline]
    prepopulated_fields = {'slug': ('name',)}

class SeasonColorInline(admin.TabularInline):
    model = SeasonColor

class SeasonAdmin(admin.ModelAdmin):
    model = Season
    list_display = ('name', 'stylesheet')
    inlines = [SeasonColorInline]

admin.site.register(SeasonalStylesheet, StylesheetAdmin)
admin.site.register(Season, SeasonAdmin)
