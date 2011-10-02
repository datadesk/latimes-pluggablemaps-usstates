from django.core.management.base import BaseCommand, CommandError
from us_states import load

class Command(BaseCommand):
    help = 'Loads data for pluggable maps of U.S. states'

    def handle(self, *args, **options):
        print 'Loading data for U.S. states'
        load.all()
        print 'Successfully loaded data for U.S. states'
