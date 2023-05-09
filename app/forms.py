from django import forms


# creating a form
class InputForm(forms.Form):
    store_id = forms.CharField(max_length=256)
