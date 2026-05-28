from rest_framework.test import APITestCase
from user.logic import valid_password


class ValidPasswordTestCase(APITestCase):
    """
    Casos de prueba para la función `valid_password` que valida contraseñas
    bajo las siguientes reglas:
    - Mínimo 8 y máximo 64 caracteres.
    - Al menos una letra mayúscula.
    - Al menos una letra minúscula.
    - Al menos un dígito.
    - Al menos un símbolo especial (ASCII 33 al 126).
    """

    def test_01_valid_password(self):
        """
        Debe retornar True cuando la contraseña tiene el formato correcto.
        """
        password = "P4$$w0rd."
        self.assertTrue(valid_password(password))

    def test_02_min_length_valid_password(self):
        """
        Debe retornar True para una contraseña válida con longitud mínima (8 caracteres).
        """
        password = "P4$$w0rd"
        self.assertTrue(valid_password(password))

    def test_03_max_length_valid_password(self):
        """
        Debe retornar True para una contraseña válida con longitud máxima (64 caracteres).
        """
        letters = ["P", "4", "$", "$", "w", "0", "r", "D"]
        password = "".join([letter * 8 for letter in letters])
        self.assertTrue(valid_password(password))

    def test_04_small_password(self):
        """
        Debe retornar False cuando la contraseña tiene menos de 8 caracteres.
        """
        password = "P4$$"
        self.assertFalse(valid_password(password))

    def test_05_big_password(self):
        """
        Debe retornar False cuando la contraseña supera los 64 caracteres.
        """
        letters = ["P", "4", "$", "w", "0", "r", "D"]
        password = "".join([letter * 10 for letter in letters])
        self.assertFalse(valid_password(password))

    def test_06_invalid_format_password(self):
        """
        Debe retornar False para contraseñas que no cumplen con los requisitos de formato.
        """
        test_cases = [
            ("password", False),  # solo minúsculas
            ("PASSWORD", False),  # solo mayúsculas
            ("$$$$$$$$", False),  # solo símbolos
        ]
        for password, expected in test_cases:
            with self.subTest(password=password):
                self.assertEqual(valid_password(password), expected)

    def test_07_permited_symbols(self):
        """
        Debe retornar True para contraseñas válidas que contienen cada uno
        de los símbolos especiales permitidos individualmente.
        """
        # ASCII: 33–47, 58–64, 91–96, 123–126 (símbolos especiales)
        permited_symbols = [chr(i) for i in range(33, 48)]
        permited_symbols += [chr(i) for i in range(58, 65)]
        permited_symbols += [chr(i) for i in range(91, 97)]
        permited_symbols += [chr(i) for i in range(123, 127)]

        for symbol in permited_symbols:
            password = f"P4ssW0rd{symbol}"
            with self.subTest(symbol=symbol):
                self.assertTrue(valid_password(password))

    def test_08_symbol_not_allowed(self):
        """
        Debe retornar False cuando la contraseña incluye un símbolo fuera del rango permitido (por ejemplo, espacio).
        """
        symbol = chr(32)  # espacio (no permitido)
        password = f"P4ss{symbol}wrd."
        self.assertFalse(valid_password(password))
