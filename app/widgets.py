from django import forms


class FileInputByOnlyfilename(forms.ClearableFileInput):
    """templateを変更"""
    template_name = 'app/widgets/file_input_by_onlyfilename.html'
