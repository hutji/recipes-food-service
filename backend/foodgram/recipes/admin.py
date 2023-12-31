from django.contrib import admin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import (Favorite, Ingredient, IngredientToRecipe, Recipe,
                     ShopList, Tag)


class IngredientInline(admin.TabularInline):
    model = IngredientToRecipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """ Админ панель управления рецептами """
    list_display = ('name', 'author', 'cooking_time',
                    'in_favorite',)
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name', 'author', 'tags')
    inlines = (IngredientInline,)
    empty_value_display = '-пусто-'
    verbose_name = 'Рецепт'
    verbose_name_plural = 'Рецепты'

    def in_favorite(self, obj: Recipe):
        return obj.favorites.count()

    in_favorite.short_description = 'В избранном'


class IngredientAdmin(admin.ModelAdmin):
    """ Админ панель управления ингредиентами """
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', )
    list_filter = ('name', )
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name',)
    empty_value_display = '-пусто-'


class FavoriteAdmin(admin.ModelAdmin):
    """ Админ панель управления подписками """
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = '-пусто-'


class ShoplistAdmin(admin.ModelAdmin):
    """ Админ панель списка покупок """
    list_display = ('recipe', 'user')
    list_filter = ('recipe', 'user')
    search_fields = ('user', )
    empty_value_display = '-пусто-'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ShopList, ShoplistAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
