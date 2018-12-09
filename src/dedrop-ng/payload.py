import os
import tempfile
import zipfile
import dedrop
import time
import dis
from binascii import hexlify
# import marshal3

print("Hi, this is the payload 2!")
import sys
print(sys.version)

pyc_file = os.environ.get('PYC_FILE')

def decrypt_pyc(pyc_file, new_pyc_file=None):
    try:
        pyc_code = dedrop.decrypt(pyc_file)
    except:
        print("[!] Failing for %s" % pyc_file)
        import traceback
        traceback.print_exc()
        return
    if not new_pyc_file:
        # new_pyc_file = pyc_file.replace(".pyc", ".npyc")
        new_pyc_file = "output.pyc"
    print("[+] writing to", new_pyc_file)
    with open(new_pyc_file, "wb") as f:
        # Note: getting the version magic right is crucial!
        # f.write(b'3\r\r\n')  # won't work when original bytecode version corresponds to python 3.5.4
        f.write(b'\x17\r\r\n')
        # We don't care about a timestamp
        f.write(b'\x00\x00\x00\x00')
        f.write(b'\x00\x00\x00\x00')  # required for modern python version
        bytecode = dedrop.bytecode(pyc_code)
        x = marshal3.dumps(pyc_code)
        f.write(x)

if pyc_file:
    decrypt_pyc(pyc_file)

pyc_path = os.environ.get('PYC_PATH')

if pyc_path:
    if not os.path.isdir(pyc_path):
        print("PYC_PATH is not a directory!")
    else:
        pyc_path = os.path.abspath(pyc_path)
        base_path = os.path.dirname(pyc_path)
        decrypted_path = os.path.join(base_path, "pyc_decrypted")
        for path, dirs, files in os.walk(pyc_path):
            for filename in [os.path.abspath(os.path.join(path, fname)) for fname in files]:
                new_filename = filename.replace(pyc_path, decrypted_path)
                current_base_path = os.path.dirname(new_filename)
                try:
                    os.makedirs(current_base_path)
                except Exception as e:
                    print(str(e))
                decrypt_pyc(filename, new_filename)

blob_path = os.environ.get('BLOB_PATH')

if blob_path:
    if not os.path.isfile(blob_path):
        print("BLOB_PATH is not a file!")
    else:
        blob_path = os.path.abspath(blob_path)
        mode = "r"

        print("\n:) :) :) Having Fun Yet?\n\n")
        time.sleep(2)

        f = zipfile.PyZipFile(blob_path, mode, zipfile.ZIP_DEFLATED)
        # base_path = os.path.dirname(blob_path)
        base_path = os.getcwd()
        base_decrypted_path = os.path.join(base_path, "pyc_decrypted")
        for filename in f.namelist():
            new_filename = os.path.join(base_decrypted_path, filename)
            current_base_path = os.path.dirname(new_filename)
            try:
                os.makedirs(current_base_path)
            except Exception as e:
                pass
            fh = tempfile.NamedTemporaryFile(delete=False)
            data = f.open(filename, "r").read()
            fh.write(data)
            tname= fh.name
            fh.close()
            decrypt_pyc(tname, new_filename)
            try:
                os.remove(tname)
            except Exception as e:
                print(str(e))

        print("\n:) :) :) w00t! \n\n")
