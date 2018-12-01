## wcwidth cmdline tool

Small helper to get wcwidth values from libc.

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

