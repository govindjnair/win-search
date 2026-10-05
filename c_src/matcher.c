#include "matcher.h"
#include <ctype.h>

int str_contains_ignore_case(const char *haystack, const char *needle) {

  if (!needle || *needle == '\0') {
    return 1;
  }

  if (!haystack) {
    return 0;
  }

  for (int i = 0; haystack[i] != '\0'; i++) {
    int j = 0;
    while (needle[j] != '\0' && haystack[i + j] != '\0') {
      if (tolower((unsigned char)haystack[i + j]) !=
          tolower((unsigned char)needle[j]))
        break;

      j++;
    }
    if (needle[j] == '\0')
      return 1;
  }

  return 0;
}