import csv

from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из csv-файла /data/ingredients.csv'

    def handle(self, *args, **options):
        print('Uploading ingredients to the database ... ', end='')
        try:
            with open('../data/ingredients.csv') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    Ingredient(
                        name=row[0],
                        measurement_unit=row[1],
                    ).save()
                print('Done')
        except FileNotFoundError:
            raise CommandError("Can't open file")
        except (IndexError, AttributeError):
            raise CommandError('Data entry error')
        except PermissionError:
            raise CommandError('File access error')
        except OSError:
            raise CommandError('File system error')
