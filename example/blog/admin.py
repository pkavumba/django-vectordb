from django.contrib import admin

from .models import Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "description")
    list_filter = ("title", "description")
    search_fields = ("title", "description")


admin.site.register(Post, PostAdmin)
