from csv import DictReader

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из csv-файла /data/ingredients.csv'

    def handle(self, *args, **options):
        try:
            reader = DictReader(open('../recipes/data/ingredients.csv'))
        except Exception:
            FileNotFoundError("Can't open file")
        if Ingredient.objects.exists():
            print('The ingredients have already been uploaded to the database')
            return
        print('Uploading ingredients to the database')
        try:
            for row in reader:
                Ingredient(
                    name=row[0],
                    measurement_unit=row[1],
                ).save()
            print('Done')
        except Exception:
            AttributeError("Can't save ingredient")
