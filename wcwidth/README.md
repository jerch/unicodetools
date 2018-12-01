## wcwidth cmdline tools

Small helper to get wcwidth values:
- wcwidth: query wcwidth directly from libc
- query_terminal.py: python script to generate data from Cursor Position Report (CPR)

### Build

```bash
#> gcc wcwidth.c -o wcwidth
```

### Generate data

```bash
#> ./wcwidth "<locale_string or empty>" <start> <end>
#> ./wcwidth "ko_KR.UTF-8" 0 0x110000 > full_unicode_korean.data
```
`start` and `end` support decimal and hexadecimal values. `end` is exclusive.
The returned data contains the wcwidth values as single hex character for every codepoint ('0' - 'F' where 'F' stands for -1). A certain value can be accessed by the string index.

The python script writes a single codepoint to the terminal and does a Cursor Position Report.
This way it is possible to get the values from emulators even without a working wcwidth in libc:

```bash
#> python query_terminal.py <start> <end> <output_file>
```
Since this approach relies on installed terminal emulators its defaults to the system locale setting.
To get values for different locale settings change those accordingly.
Other than the wcwidth tool the script cannot report -1 ('F') for control chars.
