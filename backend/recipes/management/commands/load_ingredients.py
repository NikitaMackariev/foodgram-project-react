import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из csv-файла /data/ingredients.csv'

    def handle(self, *args, **options):

        print('Loading ingredients from csv ... ', end='')
        with open('../data/ingredients.csv') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                Ingredient(
                    name=row[0],
                    measurement_unit=row[1],
                ).save()
            print('Done')
