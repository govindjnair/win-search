#include "engine.h"
#include "matcher.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

SearchIndex *index_create(size_t initial_capacity) {
  if (initial_capacity == 0) {
    initial_capacity = 16; // sensible default
  }

  // allocate memory for searchindex struct
  SearchIndex *idx = (SearchIndex *)malloc(sizeof(SearchIndex));
  if (!idx) {
    return NULL; // allocation failed
  }
  // allocate memory for the searchentry items
  idx->entries = (SearchEntry *)malloc(initial_capacity * sizeof(SearchEntry));
  if (!idx->entries) {
    free(idx);
    return NULL;
  }
  idx->count = 0;
  idx->capacity = initial_capacity;

  return idx;
}

void index_free(SearchIndex *idx) {
  if (!idx) {
    return;
  }
  // free internal array of entries first, to avoid use after free bugs
  if (idx->entries) {
    free(idx->entries);
  }
  free(idx);
}

int index_add(SearchIndex *idx, const char *title, const char *path,
              const char *category) {
  if (!idx) {
    return 0;
  }
  if (idx->count >= idx->capacity) {
    size_t new_capacity = idx->capacity * 2;
    SearchEntry *new_entries = (SearchEntry *)realloc(
        idx->entries, new_capacity * sizeof(SearchEntry));
    if (!new_entries) {
      return 0; // failed to grow, but existing entries are safe
    }
    idx->entries = new_entries;
    idx->capacity = new_capacity;
  }
  // pointer to next free slot
  SearchEntry *entry = &idx->entries[idx->count];

  // safe copy with buffer overflow protection
  snprintf(entry->title, sizeof(entry->title), "%s", title ? title : "");
  snprintf(entry->path, sizeof(entry->path), "%s", path ? path : "");
  snprintf(entry->category, sizeof(entry->category), "%s",
           category ? category : "File");

  // increment item count
  idx->count++;

  return 1; // Success
}

int index_search(const SearchIndex *idx, const char *query,
                 SearchEntry *results, int max_results) {
  if (!idx || !results || max_results <= 0) {
    return 0;
  }

  int match_count = 0;
  // loop through all items in RAM
  for (size_t i = 0; i < idx->count; i++) {
    if (match_count >= max_results) {
      break;
    }
    const SearchEntry *entry = &idx->entries[i];

    // check if query matches title or path using the matcher
    if (str_contains_ignore_case(entry->title, query) ||
        str_contains_ignore_case(entry->path, query)) {
      results[match_count] = *entry;
      match_count++;
    }
  }
  return match_count;
}
