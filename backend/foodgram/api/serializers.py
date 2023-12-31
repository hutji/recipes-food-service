from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientToRecipe, Recipe,
                            ShopList, Tag)
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Серилизатор для модели Tag."""
    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag

    def validate(self, data):
        for key, value in data.items():
            data[key] = value.sttrip('#').lower()
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор связи ингредиентов и рецепта """
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientToRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class IngredientRecipeForCreateSerializer(serializers.ModelSerializer):
    """ Сериализатор связи ингредиентов и рецепта для записи."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientToRecipe
        fields = ('id', 'amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра рецепта """
    tags = TagSerializer(read_only=False, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredienttorecipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time'
                  )

    def get_ingredients(self, obj):
        ingredients = IngredientToRecipe.objects.filter(recipe=obj)
        return IngredientRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.favorites.filter(user=request.user).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.shopping_list.filter(user=request.user).exists())


class CreateRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для создания рецепта """
    ingredients = IngredientRecipeForCreateSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Указанного тега не существует'}
    )
    image = Base64ImageField(max_length=None)
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time')

    def validate(self, data):
        if Recipe.objects.filter(
                name=data['name']).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError('Такой рецепт уже есть!')
        return data

    def validate_tags(self, tags):
        tags_list = []
        for tag in tags:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Указанного тега не существует')
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError(
                    'Теги должны быть уникальны')
            tags_list.append(tag)
            if len(tags_list) < 1:
                raise serializers.ValidationError(
                    'Отсуствуют теги')
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время готовки должно быть не меньше одной минуты')
        if cooking_time > 2880:
            raise serializers.ValidationError(
                'Время готовки должно быть не больше 2 суток')
        return cooking_time

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError(
                'Отсутствуют ингридиенты!'
            )
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    'Есть одинаковые ингредиенты!'
                )
            ingredients_list.append(ingredient_id)
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента больше 0')

        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_liist = []
        for ingredient_data in ingredients:
            ingredient_liist.append(
                IngredientToRecipe(
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount'],
                    recipe=recipe,
                )
            )
        IngredientToRecipe.objects.bulk_create(ingredient_liist)

    def create(self, validated_data):
        with transaction.atomic():
            request = self.context.get('request', None)
            tags = validated_data.pop('tags')
            ingredients = validated_data.pop('ingredients')
            recipe = Recipe.objects.create(author=request.user,
                                           **validated_data)
            recipe.tags.set(tags)
            self.create_ingredients(recipe, ingredients)
            return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        IngredientToRecipe.objects.filter(recipe=recipe).delete()
        self.create_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Серилизатор полей избранных рецептов и покупок."""

    class Meta:
        fields = (
            'name', 'text', 'cooking_time',
            'image',
        )
        model = Recipe


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов."""

    class Meta:
        fields = (
            'recipe', 'user'
        )
        model = Favorite

    def validate(self, data):
        user = data['user']
        if user.favorites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShopListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    class Meta:
        fields = (
            'recipe', 'user'
        )
        model = ShopList

    def validate(self, data):
        user = data['user']
        if user.shopping_list.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в корзину'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
