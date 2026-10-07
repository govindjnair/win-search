#include "engine.h"
#include "matcher.h"
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// temp struct to attact score to an entry
typedef struct {
  SearchEntry entry;
  int score;
} ScoredEntry;

// comparator for quick sort
static int compare_scored_entries(const void *a, const void *b) {
  const ScoredEntry *entry_a = (ScoredEntry *)a;
  const ScoredEntry *entry_b = (ScoredEntry *)b;

  return entry_b->score - entry_a->score;
}

// scoring function
static int calculate_score(const SearchEntry *entry, const char *query) {
  int score = 0;
  // title starts with query
  if (str_starts_with_ignore_case(entry->title, query)) {
    score += 100;
    if (strlen(entry->title) == strlen(query)) {
      score += 100; // exact match
    }

  }
  // substring in title
  else if (str_contains_ignore_case(entry->title, query)) {
    score += 50;
  }
  // word boundary bonus
  char space_query[64];
  snprintf(space_query, sizeof(space_query), " %s", query);
  if (score > 0 && str_contains_ignore_case(entry->title, space_query)) {
    score += 80;
  }
  // app bonus
  if (score > 0 && strcmp(entry->category, "App") == 0) {
    score += 30;
  }
  // installer penalty
  if (score > 0 && (str_contains_ignore_case(entry->path, "setup") ||
                    str_contains_ignore_case(entry->path, "installer"))) {
    score -= 60;
  }
  // fallback
  if (score == 0 && str_contains_ignore_case(entry->path, query)) {
    score += 10;
  }
  return score; // returns 0 if there is no match at all
}

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

  // if query is empty, return top items directly

  if (!query || *query == '\0') {
    int count =
        (idx->count < (size_t)max_results ? (int)idx->count : max_results);
    for (int i = 0; i < count; i++) {
      results[i] = idx->entries[i];
    }
    return count;
  }
  // allocate temp buffer for candidated to sort
  size_t candidate_capacity = 512;
  ScoredEntry *candidates =
      (ScoredEntry *)malloc(candidate_capacity * sizeof(ScoredEntry));
  if (!candidates) {
    return 0;
  }
  int candidate_count = 0;

  // Score every item in the index
  for (size_t i = 0; i < idx->count; i++) {
    int score = calculate_score(&idx->entries[i], query);
    if (score > 0) {
      candidates[candidate_count].entry = idx->entries[i];
      candidates[candidate_count].score = score;
      candidate_count++;

      if ((size_t)candidate_count >= candidate_capacity) {
        break; // reached candidate capacity
      }
    }
  }
  // score candidated by descending order
  qsort(candidates, candidate_count, sizeof(ScoredEntry),
        compare_scored_entries);
  // copy top results into the caller's output array
  int final_count =
      (candidate_count < max_results) ? candidate_count : max_results;
  for (int i = 0; i < final_count; i++) {
    results[i] = candidates[i].entry;
  }

  // free the temporary candidate buffer
  free(candidates);

  return final_count;
}
