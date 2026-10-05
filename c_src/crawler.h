#ifndef CRAWLER_H
#define CRAWLER_H

#include "engine.h"

// recursively crawls dir path and adds all the files found to 'idx'.
// max_depth limits how deep to go to subfolders and to prevent infinite loops.
// returns the total number of new items added.

int crawl_directory(SearchIndex *idx, const char *dir_path, int max_depth);

#endif
