from django import forms

class LinkedInForm(forms.Form):
    username = forms.CharField(label='LinkedIn Username', max_length=100)
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
