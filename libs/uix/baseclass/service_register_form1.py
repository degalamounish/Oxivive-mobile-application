import json
import re
import random
import sqlite3
import string

import bcrypt
from kivy import platform
from kivy.core.window import Window
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivy.properties import BooleanProperty
from kivy.clock import Clock

from server import Server
from anvil.tables import app_tables


class ServiceRegisterForm1(MDScreen):
    password_valid = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(ServiceRegisterForm1, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.on_keyboard)
        Clock.schedule_interval(self.auto_validate, 0.5)
        self.server = Server()
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

    def on_keyboard(self, instance, key, scancode, codepoint, modifier):
        if key == 27:  # Keycode for the back button on Android
            self.on_back_button()
            return True
        return False

    def show_validation_dialog(self, message):
        # Create the dialog asynchronously
        Clock.schedule_once(lambda dt: self._create_dialog(message), 0)

    def _create_dialog(self, message):
        dialog = MDDialog(
            text=f"{message}",
            elevation=0,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def on_back_button(self):
        self.manager.push_replacement("signup", "right")
        self.ids.service_provider_name.text = ""
        self.ids.service_provider_name.error = False
        self.ids.service_provider_name.helper_text = ''

        self.ids.service_provider_email.text = ""
        self.ids.service_provider_email.error = False
        self.ids.service_provider_email.helper_text = ''

        self.ids.service_provider_password.text = ""
        self.ids.service_provider_password.error = False
        self.ids.service_provider_password.helper_text = ''

        self.ids.service_provider_phoneno.text = ""
        self.ids.service_provider_phoneno.error = False
        self.ids.service_provider_phoneno.helper_text = ''

        # self.ids.service_provider_address.text = ""
        # self.ids.service_provider_address.error = False
        # self.ids.service_provider_address.helper_text = ''

    def auto_validate(self, *args):
        self.password_valid = bool(
            self.ids.service_provider_password.text and self.validate_password(self.ids.service_provider_password.text)[
                0])

    def on_password_change(self, instance, value):
        self.password_valid, hint_text = self.validate_password(value)
        if not self.password_valid:
            self.ids.service_provider_password.error = True
            self.ids.service_provider_password.helper_text = hint_text
        else:
            self.ids.service_provider_password.error = False
            self.ids.service_provider_password.helper_text = ""

    def register_validation(self):
        service_provider_name = self.ids.service_provider_name.text
        service_provider_email = self.ids.service_provider_email.text
        service_provider_password = self.ids.service_provider_password.text
        service_provider_phoneno = self.ids.service_provider_phoneno.text
        #service_provider_address = self.ids.service_provider_address.text
        random_code = self.generate_random_code()
        print(random_code)

        hash_pashword = bcrypt.hashpw(service_provider_password.encode('utf-8'), bcrypt.gensalt())
        hash_pashword = hash_pashword.decode('utf-8')
        print("hash_pashword  : ", hash_pashword)

        # Validation logic
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        is_valid_password, password_error_message = self.validate_password(service_provider_password)

        if not service_provider_name:
            self.ids.service_provider_name.error = True
            self.ids.service_provider_name.helper_text = "This field is required."
            self.ids.service_provider_name.required = True
        elif not service_provider_email or not re.match(email_regex, service_provider_email):
            self.ids.service_provider_email.error = True
            self.ids.service_provider_email.helper_text = "Invalid email format."
            self.ids.service_provider_email.required = True
        elif not is_valid_password:
            self.ids.service_provider_password.error = True
            self.ids.service_provider_password.helper_text = password_error_message
            self.ids.service_provider_password.required = True
        elif not service_provider_phoneno or len(service_provider_phoneno) != 10:
            self.ids.service_provider_phoneno.error = True
            self.ids.service_provider_phoneno.helper_text = "Invalid phone number (10 digits required)."
            self.ids.service_provider_phoneno.required = True
        #elif not service_provider_address:
            #self.ids.service_provider_address.error = True
            #self.ids.service_provider_address.helper_text = "This field is required."
            #self.ids.service_provider_address.required = True

        else:
            service_register_data = {'id': random_code, 'name': service_provider_name, 'email': service_provider_email,
                                     'phone': service_provider_phoneno,
                                     'password': hash_pashword, }
            with open("service_register_data.json", "w") as json_file:
                json.dump(service_register_data, json_file)
            try:
                print("Entering")
                if self.server.is_connected():
                    # Check if email and phone already exist in the database
                    existing_email = app_tables.oxi_users.get(oxi_email=service_provider_email)
                    existing_phone = app_tables.oxi_users.get(oxi_phone=float(service_provider_phoneno))

                    if existing_email:
                        print("email")
                        self.ids.service_provider_email.error = True
                        self.ids.service_provider_email.helper_text = "Email already registered"
                        self.ids.service_provider_email.required = True

                    elif existing_phone:
                        self.ids.service_provider_phoneno.error = True
                        self.ids.service_provider_phoneno.helper_text = "Phone number already registered"
                        self.ids.service_provider_phoneno.required = True

                    else:
                        print("table")
                        app_tables.oxi_users.add_row(
                            oxi_username=service_provider_name,
                            oxi_id=random_code,
                            oxi_email=service_provider_email,
                            oxi_password=hash_pashword,
                            oxi_phone=int(service_provider_phoneno),
                            #oxi_address=service_provider_address,
                            oxi_usertype='vendor')

                        self.manager.push("login")
                else:
                    self.show_validation_dialog("No internet connection")

            except Exception as e:
                print(e)
                self.show_validation_dialog("Error processing user data")

    # password validation
    def validate_password(self, password):
        # Check if the password is not empty
        if not password:
            return False, "Password cannot be empty"

        # Check if the password has at least 8 characters
        if len(password) < 6:
            return False, "Password must have at least 6 characters"

        # Check if the password contains both uppercase and lowercase letters
        if not any(c.isupper() for c in password) or not any(c.islower() for c in password):
            return False, "Password must contain uppercase, lowercase"

        # Check if the password contains at least one digit
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        # Check if the password contains at least one special character
        special_characters = r"[!@#$%^&*(),.?\":{}|<>]"
        if not re.search(special_characters, password):
            return False, "Password must contain a special character"

        # All checks passed; the password is valid
        return True, "Password is valid"

    def generate_random_code(self):
        prefix = "SP"
        random_numbers = ''.join(random.choices(string.digits, k=5))
        code = prefix + random_numbers

        return code
