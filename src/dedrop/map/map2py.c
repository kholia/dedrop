// vim: ts=4 expandtab

/* Quick hack to export opcode map to python */

#include <stdio.h>

#define UINT8 unsigned char

#include "../../decrypt/src/opcode.h"
#include "../../decrypt/src/opcode_map.h"

int main()
{
    unsigned int i;
    unsigned int n = sizeof(opcode_map)/sizeof(opcode_map[0]);

    printf ("opcode_map = {\n    ");
    for (i = 0; i < n; i++) {
         printf("%d : %d", i, opcode_map[i]);
         if (i < n - 1) {
             printf(", ");
         }
         if (i > 0 && i % 8 == 0) {
             printf("\n    ");    
         }
    } 
    printf("}\n");

    return 0;
}
