from django.core.management.base import BaseCommand
from prediccion.ml.train import train_and_save


class Command(BaseCommand):
    help = 'Entrena el modelo de riesgo glucémico y guarda modelo_riesgo.pkl'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n Iniciando entrenamiento del modelo de IA...\n'))
        try:
            train_and_save()
            self.stdout.write(self.style.SUCCESS('\n Modelo entrenado y guardado exitosamente.\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n Error durante el entrenamiento: {e}\n'))
            raise