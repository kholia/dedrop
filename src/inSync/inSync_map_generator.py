from inSync_opcodes import opmap as oopmap  # obfuscated opmap
from standard_opcodes import opmap

output_map = {}

for k, v in oopmap.items():
    output_map[v] = opmap[k]

print(output_map)
