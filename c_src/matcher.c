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

int str_starts_with_ignore_case(const char *str, const char *prefix) {
  if (!prefix || *prefix == '\0') {
    return 1;
  }
  if (!str) {
    return 0;
  }
  int i = 0;
  while (prefix[i] != '\0') {
    if (str[i] == '\0') {
      return 0;
    }
    if (tolower((unsigned char)str[i]) != tolower((unsigned char)prefix[i])) {
      return 0;
    }
    i++;
  }
  return 1;
}