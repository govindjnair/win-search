#include "engine.h"
#include <stdio.h>

int main(void) {
  printf("--- Testing Win-Search C Engine ---\n");

  // 1. Create the index
  SearchIndex *idx = index_create(4);

  // 2. Add some test items
  index_add(idx, "Notepad", "C:\\Windows\\System32\\notepad.exe", "App");
  index_add(idx, "Calculator", "calc.exe", "App");
  index_add(idx, "Command Prompt", "cmd.exe", "App");
  index_add(idx, "PowerShell", "powershell.exe", "App");

  printf("Total items indexed: %zu\n", idx->count);

  // 3. Search for "calc"
  SearchEntry results[5];
  int found = index_search(idx, "calc", results, 5);

  printf("\nSearch Query: 'calc' -> Found %d match(es):\n", found);
  for (int i = 0; i < found; i++) {
    printf("  [%s] %s -> %s\n", results[i].category, results[i].title,
           results[i].path);
  }

  // 4. Free the memory
  index_free(idx);
  printf("\nMemory freed cleanly!\n");

  return 0;
}
