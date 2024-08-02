from django import forms
from django.forms import ModelForm
from myapp.models import Employee, Serveur, Filiale

class EmployeeForm(ModelForm):
    filiale = forms.ModelChoiceField(
        queryset=Filiale.objects.all(),
        empty_label="Choisissez une filiale",
        help_text="Sélectionnez la filiale à laquelle l'employé appartient."
    )
    role = forms.ChoiceField(
        choices=Employee.ROLE_CHOICES,
        help_text="Sélectionnez le rôle de l'employé : Administrateur ou Utilisateur."
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Votre mot de passe'}),
        required=False,
        help_text="Le mot de passe peut être de n'importe quelle longueur et type."
    )

    class Meta:
        model = Employee
        fields = ['name', 'contact', 'email', 'filiale', 'role', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@gmail.com'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre numéro de contact'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@gmail.com'):
            raise forms.ValidationError("Veuillez utiliser une adresse email se terminant par @gmail.com.")
        return email

    def save(self, commit=True):
        employee = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            employee.set_password(password)
        if commit:
            employee.save()
        return employee

class ServeurForm(forms.ModelForm):
    class Meta:
        model = Serveur
        fields = ['nomserveur', 'adresse', 'unite', 'date', 'filiale', 'username', 'password']
        widgets = {
            'nomserveur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du serveur'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adresse IP du serveur'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'unite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unité de stockage'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'}),
            'password': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre mot de passe (laisser vide si inchangé)'})
        }

    def clean_adresse(self):
        adresse = self.cleaned_data.get('adresse')
        if Serveur.objects.filter(adresse=adresse).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Un serveur avec cette adresse existe déjà.')
        return adresse

