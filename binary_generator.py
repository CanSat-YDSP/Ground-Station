# generate a binary file, binary.bin with 259 bytes of incrementing values from 0 to 258 hex
with open("binary.bin", "wb") as f:
    f.write(bytearray(range(256)) + bytearray([67, 67, 68]))
print("binary.bin file generated with 259 bytes of incrementing values.")
