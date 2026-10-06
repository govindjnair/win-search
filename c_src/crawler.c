#include "crawler.h"
#include "engine.h"
#include "matcher.h"
#include <dirent.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

// check if a directory should be skipped
static int is_ignored_dir(const char *name) {
  // skip hidden folders like .git .venv .vscode
  if (name[0] == '.') {
    return 1;
  }
  // skip dependency and cahce folder
  if (strcmp(name, "node_modules") == 0 || strcmp(name, "__pycache__") == 0 ||
      strcmp(name, "$Recycle.Bin") == 0) {
    return 1;
  }
  return 0;
}

// check if a file should be ignored
static int is_ignored_file(const char *name) {
  // skip .gitignore, .env etc
  if (name[0] == '.') {
    return 1;
  }
  const char *ext = strrchr(name, '.');
  if (ext) {
    if (str_contains_ignore_case(ext, ".tmp") ||
        str_contains_ignore_case(ext, ".log") ||
        str_contains_ignore_case(ext, ".ini") ||
        str_contains_ignore_case(ext, ".bak") ||
        str_contains_ignore_case(ext, ".cache"))
      return 1;
  }
  return 0;
}

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
      if (!is_ignored_dir(entry->d_name) && max_depth > 0) {
        added_count += crawl_directory(idx, full_path, max_depth - 1);
      }
    }
    // if it is a regular file, check if it's an App or a File
    else if (S_ISREG(st.st_mode)) {
      if (!is_ignored_file(entry->d_name)) {
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
  }
  closedir(dir);
  return added_count;
}