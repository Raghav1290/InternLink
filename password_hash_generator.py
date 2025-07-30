"""This is the script to generate password hashes for one or more user accounts.
...
"""
from collections import namedtuple
from flask import Flask
from flask_bcrypt import Bcrypt

UserAccount = namedtuple('UserAccount', ['username', 'password'])

app = Flask(__name__)
flask_bcrypt = Bcrypt(app)

# List of users including admins, employerr and students
users = [
         # Admin UserAccount Examples
         UserAccount('admin_max', 'MaxSecure@1A!'),
         UserAccount('admin_sara', 'SaraPassw0rd#2B'),

         # Employer UserAccount Examples
         UserAccount('emp_alpha', 'AlphaCorp!3C'),
         UserAccount('emp_beta', 'BetaInnov@4D'),
         UserAccount('emp_gamma', 'GammaS0ft%5E'),
         UserAccount('emp_delta', 'DeltaLabs^6F'),
         UserAccount('emp_epsilon', 'EpsilonMkt&7G'),

         # Student UserAccount Examples
         UserAccount('stu_liam', 'LiamP@ss1H!'),
         UserAccount('stu_olivia', 'OliviaS3cure!I'),
         UserAccount('stu_noah', 'Noah_S0ftware!J'),
         UserAccount('stu_emma', 'EmmaD@ta2K!'),
         UserAccount('stu_sophia', 'SophiaGr@ph!L'),
         UserAccount('stu_jackson', 'JacksonC0mp#3M'),
         UserAccount('stu_ava', 'AvaBus!ness%4N'),
         UserAccount('stu_lucas', 'LucasEnv^5O'),
         UserAccount('stu_mia', 'MiaArch!t&6P'),
         UserAccount('stu_aidan', 'AidanC!vil*7Q'),
         UserAccount('stu_isabella', 'IsabellaCyb#8R'),
         UserAccount('stu_ethan', 'EthanF!nance$9S'),
         UserAccount('stu_chloe', 'ChloeJourn%0T'),
         UserAccount('stu_mason', 'MasonGame^1U!'),
         UserAccount('stu_harper', 'HarperHR&2V'),
         UserAccount('stu_logan', 'LoganAgri*3W'),
         UserAccount('stu_evelyn', 'EvelynDS#4X'),
         UserAccount('stu_benjamin', 'BenjaminRob!5Y'),
         UserAccount('stu_amelia', 'AmeliaPsy%6Z'),
         UserAccount('stu_alexander', 'AlexLaw^7A!'),
        ]

print('Username       | Password      | Hash                                                       | Password Matches Hash')
print('------------------------------------------------------------------------------------------------------------------')

for user in users:
    password_hash = flask_bcrypt.generate_password_hash(user.password)
    password_matches_hash = flask_bcrypt.check_password_hash(password_hash, user.password)
    print(f'{user.username:<14} | {user.password:<13} | {password_hash.decode():<58} | {password_matches_hash}')