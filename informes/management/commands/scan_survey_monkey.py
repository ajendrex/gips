from django.core.management import BaseCommand

from informes.scanners.scanner_surveymonkey import ScannerSurveyMonkey


class Command(BaseCommand):
    help = 'Scan Survey Monkey for new surveys and responses'

    def handle(self, *args, **options):
        scanner = ScannerSurveyMonkey()
        scanner.scan()
