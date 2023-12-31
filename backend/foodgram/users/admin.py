from django.contrib import admin

from .models import Follow, User
from recipes.models import ShopList, Favorite


class FollowInline(admin.TabularInline):
    model = Follow
    extra = 0
    fk_name = 'username'


class ShopListInline(admin.TabularInline):
    model = ShopList
    extra = 1


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0


class UserAdmin(admin.ModelAdmin):
    inlines = (FollowInline, ShopListInline, FavoriteInline)
    list_display = (
        'username', 'first_name', 'last_name', 'email',
    )
    search_fields = ('username',)
    list_filter = ('username', 'email')
    ordering = ('username',)
    empty_value_display = '-пусто-'
    verbose_name = 'Пользователь'
    verbose_name_plural = 'Пользователи'


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'author'
    )
    search_fields = ('username',)
    list_filter = ('username', 'author')
    ordering = ('username',)
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
