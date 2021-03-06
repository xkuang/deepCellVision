from django.core.management.base import BaseCommand, CommandError
from cellVision.models import CellImage
from django.utils import timezone
from django.conf import settings
from optparse import make_option
import os
class Command(BaseCommand):
    help = 'Cleans the database for models unused'

    option_list = BaseCommand.option_list+(
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help='Delete all models'),
)

    def handle(self, *args, **options):
        data = CellImage.objects.all()
        for i in range(len(data)):
            time_change = timezone.now() - data[i].last_accessed
            name = data[i].name
            if time_change.days > 5 or options.get('all', True):
                CellImage.objects.filter(name = name).delete()
                my_dir = settings.MEDIA_ROOT
                for fname in os.listdir(my_dir):
                    if fname.startswith(name):
                        os.remove(os.path.join(my_dir, fname))
                my_dir +='/classes/'
                for fname in os.listdir(my_dir):
                    if fname.startswith(name):
                        os.remove(os.path.join(my_dir, fname))
        return

