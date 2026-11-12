from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Album, Article, Comment, ContactMessage, Devotional, HeroSlide,
    Lesson, Like, PastorProfile, PrayerRequest, Sermon,
)

MODELS = {'sermon': Sermon, 'lesson': Lesson, 'devotional': Devotional}


def thumb(obj):
    src = obj.cover_src
    return format_html('<img src="{}" style="height:44px;border-radius:6px"/>', src) if src else '—'


thumb.short_description = 'Cover'


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'video_url', 'order', 'published')
    list_editable = ('order', 'published')


@admin.register(Sermon)
class SermonAdmin(admin.ModelAdmin):
    list_display = (thumb, 'title', 'speaker', 'date', 'category', 'published')
    list_filter = ('published', 'category')
    search_fields = ('title', 'speaker')
    list_editable = ('published',)
    fieldsets = (
        (None, {'fields': ('title', 'speaker', 'date', 'category', 'description')}),
        ('Video', {'fields': ('youtube_url',)}),
        ('Cover image', {'fields': ('cover', 'cover_url')}),
        ('Visibility', {'fields': ('published',)}),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (thumb, 'title', 'quarter', 'date_range', 'published')
    list_filter = ('quarter', 'published')
    search_fields = ('title', 'quarter')
    list_editable = ('published',)
    fieldsets = (
        (None, {'fields': ('title', 'quarter', 'date_range', 'start_date', 'teacher', 'description')}),
        ('Lesson video (YouTube)', {'fields': ('youtube_url',)}),
        ('Lesson PDF', {'fields': ('pdf', 'pdf_url')}),
        ('Cover image', {'fields': ('cover', 'cover_url')}),
        ('Visibility', {'fields': ('published',)}),
    )


@admin.register(Devotional)
class DevotionalAdmin(admin.ModelAdmin):
    list_display = (thumb, 'title', 'author', 'date', 'scripture', 'published')
    list_filter = ('published', 'category', 'author')
    search_fields = ('title', 'author', 'scripture')
    list_editable = ('published',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (thumb, 'title', 'section', 'author', 'date', 'published')
    list_filter = ('section', 'published', 'category')
    search_fields = ('title', 'author')
    list_editable = ('published',)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = (thumb, 'title', 'date', 'location', 'published')
    list_filter = ('published',)
    search_fields = ('title', 'location')
    list_editable = ('published',)
    fieldsets = (
        (None, {'fields': ('title', 'date', 'location', 'description')}),
        ('Photo album link', {'fields': ('photos_url',),
                              'description': 'Photos are NOT stored on this website. Upload the photos to Pixieset / Google Photos '
                                             'and paste that album link here. Only the cover image below is stored.'}),
        ('Cover image (the only file stored on Cloudinary)', {'fields': ('cover', 'cover_url')}),
        ('Visibility', {'fields': ('published',)}),
    )


@admin.register(PastorProfile)
class PastorAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
    fieldsets = (
        (None, {'fields': ('name', 'title', 'short_intro', 'quote')}),
        ('Photo', {'fields': ('photo', 'photo_url')}),
        ('Biography', {'fields': ('biography',)}),
    )

    def has_add_permission(self, request):
        return not PastorProfile.objects.exists()  # only ever one profile

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PrayerRequest)
class PrayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created', 'prayed_for')
    list_filter = ('prayed_for',)
    list_editable = ('prayed_for',)
    search_fields = ('name', 'email', 'request')


@admin.register(ContactMessage)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created', 'handled')
    list_filter = ('handled',)
    list_editable = ('handled',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'on_item', 'short', 'approved', 'created')
    list_filter = ('kind', 'approved')
    list_editable = ('approved',)
    search_fields = ('text', 'user__email')
    actions = ['hide', 'show']

    def short(self, obj):
        return obj.text[:80]

    def on_item(self, obj):
        item = MODELS[obj.kind].objects.filter(pk=obj.object_id).first()
        return str(item) if item else f'#{obj.object_id}'

    on_item.short_description = 'Commented on'

    @admin.action(description='Hide selected comments')
    def hide(self, request, queryset):
        queryset.update(approved=False)

    @admin.action(description='Show selected comments')
    def show(self, request, queryset):
        queryset.update(approved=True)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'object_id', 'created')
    list_filter = ('kind',)
