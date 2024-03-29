import argparse
import datetime
import itertools
import os
import re
import time
from zipfile import ZipFile, BadZipFile


class ZipForcer:
    def __init__(self, input_zip, files, password_alphabet, password_dictionary, password_length, output_path, verbose):
        self.__input_zip = input_zip
        self.__files = files
        self.__password_alphabet = password_alphabet
        self.__password_dictionary = password_dictionary
        self.__password_length = password_length
        self.__verbose = verbose
        self.__output_path = output_path
        self.__tries = 0
        self.__tries_since_last_second = self.__tries
        self.__start_time = None
        self.__last_second_time = None
        self.__my_zip = None

    def brute_force_zip(self):
        try:
            self.__start_time = time.time()
            self.__last_second_time = self.__start_time

            with ZipFile(self.__input_zip) as self.__my_zip:
                # Check if files are subset of namelist()
                for f in self.__files:
                    if f not in self.__my_zip.namelist():
                        print('All files have to be elements of the zip.')
                        return

                # Use random password generated by using the alphabet
                if self.__password_alphabet:
                    print(f'Now cracking the password of \'{self.__input_zip}\' '
                          f'while using alphabet: \'{self.__password_alphabet}\'.')

                    # Brute force all password between 1 and length characters long
                    for i in range(1, self.__password_length + 1):
                        generator = itertools.product(self.__password_alphabet, repeat=i)
                        for letter in generator:
                            letter = ''.join(letter)

                            try:
                                self.__try_password(letter)
                                return
                            except RuntimeError:
                                # Just ignore wrong passwords ;)
                                pass
                            except BadZipFile:
                                # Remove files extracted but which are broken
                                for f in self.__files:
                                    if os.path.exists(f):
                                        os.remove(f)

                    print('\rNo valid password found for given length. Maybe try to increase the possible length.')
                else:
                    print(f'Now cracking the password of \'{self.__input_zip}\' '
                          f'while using dictionary:\'{self.__password_dictionary}\'.')

                    try:
                        with open(self.__password_dictionary, 'r') as dict_file:
                            for word in dict_file:
                                try:
                                    self.__try_password(word.rstrip())
                                    return
                                except RuntimeError:
                                    # Just ignore wrong passwords ;)
                                    pass
                                except BadZipFile:
                                    # Remove files extracted but which are broken
                                    for f in self.__files:
                                        if os.path.exists(f):
                                            os.remove(f)
                    except OSError:
                        print('Could not find dictionary file. Please specify a valid path')
        except FileNotFoundError:
            print('Could not find zip file. Please specify a valid path.')
        except KeyboardInterrupt:
            print('\rProgram was exited by keyboard interrupt.')
            self.__save_progress()

    def __print_progress(self, password):
        if time.time() - self.__last_second_time >= 1:
            self.__last_second_time = time.time()

            # Ensures line is completely refreshed
            print('\r                                          ', end='')
            print(f'\rPassword: \'{password}\'. pw/s: {self.__tries_since_last_second}', end='')

            self.__tries_since_last_second = 0

    def __try_password(self, password):
        self.__tries += 1
        self.__tries_since_last_second += 1

        # Show verbose output (password and passwords per second)
        if self.__verbose:
            self.__print_progress(password)

        self.__my_zip.extractall(members=self.__files, pwd=password.encode('utf-8'), path=self.__output_path)

        # Only executed when extractall doesn't throw
        end_time = time.time()
        elapsed_time = end_time - self.__start_time
        time_unit = 'seconds'

        # Format elapsed time
        if elapsed_time < 1:
            elapsed_time *= 1000
            time_unit = 'milliseconds'

        print(f'\rSuccess! The correct password is: \'{password}\'.')
        print(f'Needed {elapsed_time} {time_unit} and {self.__tries:,} tries.')

        self.__my_zip.close()

    def __save_progress(self):
        tokens = re.split('/', self.__input_zip)
        sanitized_name = tokens[-1]
        output_filename = sanitized_name + '_' + str(datetime.datetime.now().date())
        with open(output_filename, 'x', encoding='utf-8') as output_file:
            output_file.write(self.__input_zip)
            output_file.write(self.__files)

    def __restore_progress(self, path_to_progress_file):
        with open(path_to_progress_file, 'r') as progress_file:
            pass


def parse_arguments():
    parser = argparse.ArgumentParser(description='Brute force the password of given ZIP file.')

    parser.add_argument('input', metavar='INPUT', type=str,
                        help='zip file whose password should be guessed')
    parser.add_argument('files', metavar='FILES', type=str, nargs='+',
                        help='a file that should be extracted from zip')
    parser.add_argument('-D', metavar='dictionary', type=str,
                        help='a file that contains passwords that should be tried (separated by newlines)')
    parser.add_argument('-c', action='store_true',
                        help='include lowercase letters in password alphabet')
    parser.add_argument('-u', action='store_true',
                        help='include uppercase letters in password alphabet')
    parser.add_argument('-d', action='store_true',
                        help='include digits in password alphabet')
    parser.add_argument('-s', action='store_true',
                        help='include special characters in password alphabet (can be VERY slow)')
    parser.add_argument('-l', metavar='length', type=int, default=8,
                        help='maximum length of the brute forced password (default is 8 characters)')
    parser.add_argument('-o', metavar='output', type=str,
                        help='path where to save extracted files')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    zip_forcer = None

    # Set default alphabet
    alphabet = ''

    if args.c:
        alphabet += 'abcdefghijklmnopqrstuvwxyz'

    if args.u:
        alphabet += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    if args.d:
        alphabet += '0123456789'

    if args.s:
        alphabet += ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    # Decide if to use the dictionary or generate the passwords
    if alphabet == '':
        if not args.D:
            print('You need to specify at least one group to be included in the password alphabet or a dictionary!')
        else:
            zip_forcer = ZipForcer(args.input, args.files, None, args.D, args.l, args.o, args.verbose)
    else:
        if not args.D:
            zip_forcer = ZipForcer(args.input, args.files, alphabet, None, args.l, args.o, args.verbose)
        else:
            print('WARNING: when you set a dictionary parameters affecting the alphabet are ignored.')
            zip_forcer = ZipForcer(args.input, args.files, None, args.D, args.l, args.o, args.verbose)

    if zip_forcer:
        zip_forcer.brute_force_zip()
