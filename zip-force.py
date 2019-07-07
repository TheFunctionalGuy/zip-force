import argparse
import itertools
import os
import time
from zipfile import ZipFile, BadZipFile


# TODO: save progress in file and specify output path
def brute_force_zip(input_zip, files, password_alphabet, length, verbose):
    try:
        # Set all necessary variables
        tries = 0
        tries_since_last_second = 0
        start_time = time.time()
        last_second_time = start_time

        try:
            with ZipFile(input_zip) as myzip:
                # Check if files are subset of namelist()
                for f in files:
                    if f not in myzip.namelist():
                        print('All files have to be elements of the zip.')
                        return

                print(f'Now cracking the password of \'{input_zip}\' while using alphabet: \'{alphabet}\'.')

                # Brute force all password between 1 and length characters long
                for i in range(1, length + 1):
                    for letter in itertools.product(password_alphabet, repeat=i):
                        letter = ''.join(letter)

                        # Show verbose output (password and passwords per second)
                        if verbose:
                            if time.time() - last_second_time >= 1:
                                last_second_time = time.time()

                                # Ensures line is completely refreshed
                                print('\r                                          ', end='')
                                print(f'\rPassword: \'{letter}\'. pw/s: {tries_since_last_second}', end='')

                                tries_since_last_second = 0
                        try:
                            tries += 1
                            tries_since_last_second += 1

                            myzip.extractall(members=files, pwd=letter.encode('utf-8'))

                            # Only executed when extractall doesn't throw
                            end_time = time.time()
                            elapsed_time = end_time - start_time
                            time_unit = 'seconds'

                            # Format elapsed time
                            if elapsed_time < 1:
                                elapsed_time *= 1000
                                time_unit = 'milliseconds'

                            print(f'\rSuccess! The correct password is: \'{letter}\'.')
                            print(f'Needed {elapsed_time} {time_unit} and {tries} tries.')
                            myzip.close()
                            return
                        except RuntimeError:
                            pass
                        except BadZipFile:
                            # Remove files extracted but which are broken
                            for f in files:
                                if os.path.exists(f):
                                    os.remove(f)
                print('\rNo valid password found for given length. Maybe try to increase the possible length.')
        except FileNotFoundError:
            print('The given zip file does not exist.')
    except KeyboardInterrupt:
        print('\rProgram was exited by keyboard interrupt.')


def parse_arguments():
    parser = argparse.ArgumentParser(description='Brute force the password of given ZIP file.')

    parser.add_argument('input', metavar='INPUT', type=str,
                        help='zip file whose password should be guessed')
    parser.add_argument('files', metavar='FILES', type=str, nargs='+',
                        help='a file that should be extracted from zip')
    parser.add_argument('-c', action='store_true',
                        help='include lowercase letters in password alphabet')
    parser.add_argument('-u', action='store_true',
                        help='include uppercase letters in password alphabet')
    parser.add_argument('-d', action='store_true',
                        help='include digits in password alphabet')
    parser.add_argument('-s', action='store_true',
                        help='include special characters in password alphabet')
    parser.add_argument('-l', '--length', type=int, default=8,
                        help='maximum length of the brute forced password (default is 8 characters)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    # Set default alphabet
    alphabet = ''

    if args.c:
        alphabet += 'abcdefghijklmnopqrstuvwxyz'

    if args.u:
        alphabet += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    if args.d:
        alphabet += '0123456789'

    # TODO: select special characters
    if args.s:
        alphabet += ''

    # Only
    if alphabet is '':
        print('You need to specify at least one group to be included in the alphabet!')
    else:
        brute_force_zip(args.input, args.files, alphabet, args.length, args.verbose)
