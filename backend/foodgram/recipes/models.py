from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    """Теги рецептов."""
    name = models.CharField('Название', max_length=200, unique=True)
    color = models.CharField(
        'Цвет', max_length=7, unique=True,
    )
    slug = models.SlugField('Слаг', unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField('Название', max_length=100, db_index=True)
    measurement_unit = models.CharField('Еденица измерения', max_length=30)

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name[:10]} {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта."""
    name = models.CharField('Название', max_length=200)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(
                1, message='Минимальное время готовки не менее 1 минуты'),
            MaxValueValidator(600)
        ]
    )
    image = models.ImageField('Изображение', upload_to='recipes/image/')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='автор',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, through='TagToRecipe',
        verbose_name=('Теги'),
        related_name='recipes'
    )

    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientToRecipe',
        verbose_name='Ингридиенты',
        related_name='recipes'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = ('Рецепт')
        verbose_name_plural = ('Рецепты')
        constraints = [
            models.UniqueConstraint(
                fields=['text', 'author'],
                name='unique_text_author'
            )
        ]

    def __str__(self):
        return self.name[:10]


class TagToRecipe(models.Model):
    """Доп. таблица для связи тегов и рецептов."""
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, verbose_name='тег',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='рецепт',
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.tag} + {self.recipe}'


class FavoriteShoppingCart(models.Model):
    """ Связывающая модель списка покупок и избранного. """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user} :: {self.recipe}'


class Favorite(FavoriteShoppingCart):
    """ Модель добавления в избранное. """

    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

        def __str__(self):
            return (f' рецепт {Favorite.recipe}'
                    f'в избранном пользователя {Favorite.user}')


class ShopList(FavoriteShoppingCart):
    """Модель списка покупок."""

    class Meta:
        default_related_name = 'shopping_list'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'

    def __str__(self):
        return (f' рецепт {ShopList.recipe}'
                f'в корзине пользователя {ShopList.user}')


class IngredientToRecipe(models.Model):
    """Доп. таблица для связи ингредиентов и рецептов."""
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='рецепт',
        related_name='ingredienttorecipe'
    )

    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество ингредиента',
        default=1
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return f'{self.ingredient} + {self.recipe}'
