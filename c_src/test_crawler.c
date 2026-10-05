#include "crawler.h"
#include "engine.h"
#include <stdio.h>

int main(void) {
  printf("--- Testing Real Filesystem Crawler ---\n");

  // 1. Create index
  SearchIndex *idx = index_create(32);

  // 2. Crawl our current project folder! (max depth 3)
  printf("Crawling project directory...\n");
  int added = crawl_directory(idx, ".", 3);
  printf("Successfully crawled and indexed %d files!\n", added);

  // 3. Search for "engine"
  SearchEntry results[10];
  int found = index_search(idx, "engine", results, 10);

  printf("\nSearch Query: 'engine' -> Found %d matches:\n", found);
  for (int i = 0; i < found; i++) {
    printf("  [%s] %s -> %s\n", results[i].category, results[i].title,
           results[i].path);
  }

  // 4. Free memory
  index_free(idx);
  printf("\nClean exit!\n");
  return 0;
}
