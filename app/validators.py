from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible 
class FileSizeValidator:
    def __init__(self, val, byte_type="mb"):
        assert byte_type in ["b", "kb", "mb", "gb"]
        if byte_type == "b":
            self._upper_byte_size = val
        elif byte_type == "kb":
            self._upper_byte_size = 1024 * val
        elif byte_type == "mb":
            self._upper_byte_size = (1024 ** 2) * val
        elif byte_type == "gb":
            self._upper_byte_size = (1024 ** 3) * val
        self._err_message = f"アップロードファイルは{val}{byte_type.upper()}未満にしてください."

    def __call__(self, file_val):
        byte_size = file_val.size
        if byte_size > self._upper_byte_size:
            raise ValidationError(message=self._err_message)
    
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and (self._upper_byte_size == other._upper_byte_size)
        )