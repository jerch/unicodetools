#include <stdio.h>
#include <wchar.h>
#include <locale.h>
#include <string.h>

/* single hex char alphabet */
char ALPHABET[] = "0123456789ABCEDF";

int convert_num(const char *s) {
    int result;
    int length = strlen(s);
    if (length <= 0) {
        return -1;
    }
    if (length > 2 && s[0] == 48 && s[1] == 120) {
        sscanf(s, "%x", &result);
    } else {
        sscanf(s, "%d", &result);
    }
    return result;
}

int main(int argc, char* argv[])
{
    if (argc != 4) {
        printf("wrong arguments, usage: wcwidth <locale> <start> <end>\n");
        return 1;
    }

    /* arg1 - locale setting */
    setlocale(LC_CTYPE, argv[1]);

    /* arg2 + arg3 - start + end */
    int start = convert_num(argv[2]);
    int end = convert_num(argv[3]);
    int length = end - start;
    if (start < 0 || end < 0 || length <= 0) {
        printf("error: wrong start/end values\n");
        return 1;
    }

    char buffer[length + 1];
    buffer[length] = '\0';

    int i;
    for (i = 0; i < length; ++i) {
        buffer[i] = ALPHABET[(wcwidth((wchar_t) i + start) + 16) & 15];
    }
    printf("%s", buffer);
    
    return 0;
}

