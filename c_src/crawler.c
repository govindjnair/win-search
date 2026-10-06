#include "crawler.h"
#include "engine.h"
#include "matcher.h"
#include <dirent.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

int crawl_directory(SearchIndex *idx, const char *dir_path, int max_depth) {
  if (!idx || !dir_path || max_depth < 0) {
    return 0;
  }
  DIR *dir = opendir(dir_path);
  if (!dir) {
    return 0; // folder doesn't exist or access denied
  }

  int added_count = 0;
  struct dirent *entry;

  // loop through the items in this dir
  while ((entry = readdir(dir)) != NULL) {
    // skip "." and ".."
    if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
      continue;
    }
    // build the full path
    char full_path[1024];
    snprintf(full_path, sizeof(full_path), "%s/%s", dir_path, entry->d_name);

    // query the file info
    struct stat st;
    if (stat(full_path, &st) != 0) {
      continue; // couldn't read file info , permission denied
    }
    // if it is a subfolder, recurse and go deeper
    if (S_ISDIR(st.st_mode)) {
      if (max_depth > 0) {
        added_count += crawl_directory(idx, full_path, max_depth - 1);
      }
    }
    // if it is a regular file, check if it's an App or a File
    else if (S_ISREG(st.st_mode)) {
      const char *ext = strrchr(entry->d_name, '.');
      const char *category = "File";

      if (ext && (str_contains_ignore_case(ext, ".lnk") ||
                  str_contains_ignore_case(ext, ".exe"))) {
        category = "App";
      }

      index_add(idx, entry->d_name, full_path, category);
      added_count++;
    }
  }
  closedir(dir);
  return added_count;
}