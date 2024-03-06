from datetime import datetime

from django.core.management import BaseCommand

from informes.scanners.scanner_surveymonkey import ScannerSurveyMonkey


class Req:
    pass


class Command(BaseCommand):
    help = 'Scan Survey Monkey for new surveys and responses'

    def handle(self, *args, **options):
        scanner = ScannerSurveyMonkey(Req())
        from_dt = datetime(2012, 12, 12)
        pruebas, errores = scanner.scan_pruebas(from_dt)

        for prueba in pruebas:
            print("descargada la prueba ", prueba)

        for error in errores:
            print("error en la prueba ", error)
