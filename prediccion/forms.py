from django import forms
import re

class CuestionarioForm(forms.Form):
    
    ya_avisado = forms.BooleanField(required=False, widget=forms.HiddenInput(), initial=False)
    
    
    nombre = forms.CharField(
                            label='Nombre', max_length=100, required=True,
                             error_messages={'required': 'Este campo es obligatorio.'}
                             )
    edad = forms.IntegerField(
                            label="Edad", min_value=1, max_value=120, required=True,
                            error_messages={'required': 'Este campo es obligatorio.'}
                            )
    sexo = forms.ChoiceField(choices=[('H', 'Hombre'), ('M', 'Mujer'), ('O', 'Otro')])
    peso = forms.DecimalField(
                            label="Peso (kg)", max_digits=5, decimal_places=2, required=True,
                            error_messages={'required': 'Este campo es obligatorio.'}
                            )
    estatura = forms.DecimalField(
                                label="Estatura (cm)", max_digits=5, decimal_places=2, required=True,
                                error_messages={'required': 'Este campo es obligatorio.'}
                                )
    antecedentes_familiares = forms.MultipleChoiceField(
                            label="¿Tienes antecedentes familiares cercanos ( padres/hermanos ) de enfermedades crónicas? (Selecciona todas las que correspondan)",
                            choices=[
                                ('diabetes', 'Diabetes tipo 2'),
                                ('hipertension', 'Hipertensión'),
                                ('cardiovascular', 'Enfermedades cardiovasculares'),
                                ('colesterol', 'Colesterol alto / Hipercolesterolemia'),
                                ('ninguno', 'No tengo antecedentes familiares')
                                ],
                                widget=forms.CheckboxSelectMultiple,
                                required=False
                            )


    consumo_ultraprocesados = forms.ChoiceField(
        label="¿Con qué frecuencia consumes alimentos ultraprocesados? (Ej: snacks, comida rápida, productos empacados)",
        choices=[('N', 'Nunca'), ('1-2', '1-2 veces por semana'), ('3-5', '3-5 veces por semana'), ('A', 'A diario')]
    )
    consumo_frutas_verduras = forms.ChoiceField(
        label="¿Consumes frutas y verduras diariamente?",
        choices=[('S', 'Sí'), ('N', 'No')]
    )
    desayuno_regular = forms.ChoiceField(
        label="¿Desayunas regularmente cada mañana?",
        choices=[('S', 'Sí'), ('N', 'No')]
    )
    comidas_principales = forms.ChoiceField(
        label="¿Cuántas comidas principales haces al día? (Desayuno, almuerzo, cena)",
        choices=[('1', '1'), ('2', '2'), ('3', '3')]
    )
    bebidas_azucaradas = forms.ChoiceField(
        label="¿Con qué frecuencia consumes bebidas azucaradas? (Ej: gaseosas, jugos artificiales)",
        choices=[('N', 'Nunca'), ('R', 'Rara vez'), ('V', 'Varias veces por semana'), ('A', 'A diario')]
    )
    consumo_grasas_saturadas = forms.ChoiceField(
        label="¿Con qué frecuencia consumes alimentos con grasas saturadas? (Ej: fritos, embutidos, productos de pastelería)",
        choices=[('N', 'Nunca'), ('R', 'Rara vez'), ('V', 'Varias veces por semana'), ('A', 'A diario')]
    )
    consumo_integrales = forms.ChoiceField(
        label="¿Qué tan frecuente consumes productos integrales? (Ej: arroz integral, avena, pan integral)",
        choices=[('S', 'Siempre'), ('A', 'A veces'), ('C', 'Casi nunca'), ('N', 'Nunca')]
    )

    
    ejercicio_regular = forms.ChoiceField(
        label="¿Haces ejercicio regularmente?",
        choices=[('S', 'Sí'), ('N', 'No')])
    estres_cronico = forms.ChoiceField(
        label="¿Sufres de estres cronico? (Estrés que persiste durante un largo período, como dias o semanas)",
        choices=[('S', 'Sí'), ('N', 'No')])
    dormir_7_horas = forms.ChoiceField(
        label="¿Duermes como mínimo 7 horas diarias?",
        choices=[('S', 'Sí'), ('N', 'No')])

   
    cambios_peso = forms.ChoiceField(
        label="¿Has sufrido cambios de peso?",
        choices=[('S', 'Sí, he subido'), ('B', 'Sí, he bajado'), ('N', 'No')])
    sensacion_debilidad = forms.ChoiceField(
        label="¿Frecuentas sensación de debilidad física?",
        choices=[('S', 'Sí'), ('N', 'No')])
    dolor_estomacal = forms.ChoiceField(
        label="¿Padeces dolor estomacal frecuentemente?",
        choices=[('S', 'Sí'), ('N', 'No')])
    examenes_sangre = forms.ChoiceField(
        label="¿Hace poco te has hecho exámenes de sangre?",
        choices=[('T', 'Sí, todos normales'), ('A', 'Sí, algunos alterados'), ('N', 'No me he hecho exámenes')])

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not re.match("^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$", nombre):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return nombre
        
    def clean_edad(self):
        edad = self.cleaned_data.get('edad')
        if edad < 5 or edad > 120:
            raise forms.ValidationError("La edad debe estar entre 5 y 100 años.")
        return edad    
        
    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso < 25 or peso > 300:
            raise forms.ValidationError("El peso debe estar entre 25 y 250 kg.")
        return peso    
        
    def clean_estatura(self):
        estatura = self.cleaned_data.get('estatura')
        if estatura < 80 or estatura > 250:
            raise forms.ValidationError("La estatura debe estar entre 80 y 250 cm.")
        return estatura    
        
    def clean(self):
        cleaned_data = super().clean()  
        errores = []

        ya_avisado = cleaned_data.get("ya_avisado")

        ejercicio = cleaned_data.get("ejercicio_regular")
        fatiga = cleaned_data.get("sensacion_debilidad")
        if ejercicio == 'S' and fatiga == 'S':
            if not ya_avisado:
               
                self.data = self.data.copy()
                self.data['ya_avisado'] = True 
                self.add_error('ejercicio_regular', 'Haces ejercicio pero reportas fatiga. Verifica tus datos y vuelve a enviarlos si es correcto.')
                
        estres = cleaned_data.get("estres_cronico")
        dormir_bien = cleaned_data.get("dormir_7_horas")
        if estres == 'S' and dormir_bien == 'S':
            if not ya_avisado:
                self.data = self.data.copy()
                self.data['ya_avisado'] = True
                self.add_error('estres_cronico', 'Estás estresado pero duermes bien. Verifica tus datos y vuelve a enviarlos si es correcto.')

        numero_comidas = cleaned_data.get("comidas_principales")
        desayuno_regular = cleaned_data.get("desayuno_regular")
        if numero_comidas in ['3', '4'] and desayuno_regular == 'N':
            if not ya_avisado:
                self.data = self.data.copy()
                self.data['ya _avisado'] = True
                self.add_error('comidas_principales', 'Dices que haces varias comidas al día pero no desayunas. Verifica tus datos y vuelve a enviarlos si es correcto.')

        consumo_frutas_verduras = cleaned_data.get("consumo_frutas_verduras")
        cambios_peso = cleaned_data.get("cambios_peso")
        if consumo_frutas_verduras == 'S' and cambios_peso == 'S':
            if not ya_avisado:
                self.data = self.data.copy()
                self.data['ya_avisado'] = True
                self.add_error('consumo_frutas_verduras', 'Comes frutas y verduras, pero reportas cambios de peso. ¿Es correcto? Verifica y vuelve a enviarlos si es correcto.')

        return cleaned_data

