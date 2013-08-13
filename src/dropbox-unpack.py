import zipfile

fileName = "Dropbox.exe"
#fileName = "cx_Freezed"
mode = "r"
f = zipfile.PyZipFile(fileName, mode, zipfile.ZIP_DEFLATED)
#print f.infolist()
print f.namelist()
f.extractall("pyc_orig")


