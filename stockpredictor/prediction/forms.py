from django import forms
from .models import StockPrediction,Watchlist
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "phone", "city", "country", "bio", "avatar"]
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()

class StockPredictionForm(forms.ModelForm):
    class Meta:
        model = StockPrediction
        fields = ['symbol', 'start_date', 'end_date']
        widgets = {
            'symbol': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'POWERGRID.NS'
            }),
            'start_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'  #calendar picker
                },
                format='%Y-%m-%d'  # HTML5 expects yyyy-mm-dd
            ),
            'end_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'  #calendar picker
                },
                format='%Y-%m-%d'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept both dd-mm-yyyy and yyyy-mm-dd formats
        self.fields['start_date'].input_formats = ['%d-%m-%Y', '%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%d-%m-%Y', '%Y-%m-%d']

    def clean_symbol(self):
        return self.cleaned_data['symbol'].strip().upper()
    
class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = ["symbol", "exchange", "group", "notes", "target_above", "target_below"]
        widgets = {
            "symbol": forms.TextInput(attrs={"placeholder": "Enter Stock Symbol (e.g., POWERGRID)"}),
            "exchange": forms.TextInput(attrs={"placeholder": "NS"}),
            "group": forms.TextInput(attrs={"placeholder": "Optional group (e.g., NIFTY50)"}),
            "notes": forms.TextInput(attrs={"placeholder": "Optional note"}),
        }