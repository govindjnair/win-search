#ifndef ENGINE_H
#define ENGINE_H

#include <stddef.h>

// A single item
typedef struct {
  char title[128];
  char path[512];
  char category[32]; // app or folder
} SearchEntry;

// Dynamic array that holds everything in the RAM
typedef struct {
  SearchEntry *entries; // pointer to the array of entries
  size_t count;         // how many items currently saved
  size_t capacity;      // total slots allocated in memory
} SearchIndex;

// function prototypes
SearchIndex *index_create(size_t initial_capacity);
int index_add(SearchIndex *idx, const char *title, const char *path,
              const char *category);
void index_free(SearchIndex *idx);

// search functions fills results array and returns how many matches are found
int index_search(const SearchIndex *idx, const char *query,
                 SearchEntry *results, int max_results);

int index_save_file(const SearchIndex *idx, const char *filepath);
SearchIndex *index_load_file(const char *filepath);

#endif // ENGINE_H