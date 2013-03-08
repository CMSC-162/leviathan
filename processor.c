#include <stdint.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdbool.h>

#define ACTION_INIT 1
#define ACTION_LINK 2
#define ACTION_STATS 3
#define ACTION_SIMULATION 4

#define MAX_NUMBER_OF_ARTICLES (1 << 24)

typedef struct {
  uint32_t article_id;
  uint32_t incoming_links, outgoing_links;
  uint32_t title_offset;
  uint32_t outgoing_offset;
  uint32_t incoming_offset;
} article;

int index_fd, data_fd;
FILE * input_file;
int action;
article * articles;

int usage() {
  printf("Usage: processor { init ./titles.txt | link { in | out } ./links.txt | stats | simulate }\n");
  return 1;
}

int main(int argc, char ** argv) {
  if (argc == 1)
    return usage();
  
  char * operation = argv[1];
  bool incoming;
   
  if (strcmp(operation, "init") == 0) {
    if (argc != 3) return usage();
    
    action = ACTION_INIT;
    
    if (strcmp(argv[2], "-") == 0) {
      input_file = stdin;
    } else {
      input_file = fopen(argv[2], "r");
      
      if (input_file < 0) {
        fprintf(stderr, "%s: %s: %s\n", argv[0], argv[2], strerrror(errno));
        exit(1);
      }
    }
  } else if (strcmp(operation, "link") == 0) {
    if (argc != 4) return usage();
    
    action = ACTION_LINK;
    
    if (strcmp(argv[2], "in") == 0)
      incoming = true;
    else if (strcmp(argv[2], "out") == 0)
      incoming = false;
    else
      return usage();
    
    if (strcmp(argv[3], "-") == 0) {
      input_file = stdin;
    } else {
      input_file = fopen(argv[3], "r");
      
      if (input_file < 0) {
        fprintf(stderr, "%s: %s: %s\n", argv[0], argv[3], strerrror(errno));
        exit(1);
      }
    }
    
  } else if (strcmp(argv[1], "stats") == 0) {
    action = ACTION_STATS;
  } else if (strcmp(argv[1], "simulate") == 0) {
    action = ACTION_SIMULATION;
  } else {
    return usage();
  }
  
  int index_fd = open("./index_file", O_RDWR | O_CREAT, (mode_t)0600);
  
  if (index_fd < 0) {
    fprintf(stderr, "%s: %s: %s\n", argv[0], "./index_file", strerrror(errno));
    exit(1);
  }

  int data_fd = open("./data_file", O_RDWR | O_CREAT, (mode_t)0600);
  
  if (data_fd < 0) {
    fprintf(stderr, "%s: %s: %s\n", argv[0], "./index_file", strerrror(errno));
    exit(1);
  }
  
  lseek(index_fd, MAX_NUMBER_OF_ARTICLES * sizeof(article), SEEK_SET);
  write(index_fd, "", 1);
  lseek(index_fd, 0, SEEK_END);
  
  article * articles = mmap(0, MAX_NUMBER_OF_ARTICLES * sizeof(article),
                               PROT_READ | PROT_WRITE, MAP_SHARED, index_fd, 0);
  article * current_article = articles - 1;
  
  uint32_t links_capacity = 1024;
  
  if (action == ACTION_INIT) {
    uint32_t page_id;
    char title[1024]; // be very careful with this!
    
    while (fscanf(input_file, "%d", &page_id) != EOF) {
      fgetc(input_file);
      fgets(title, 1024, input_file);
      
      uint32_t offset = lseek(data_fd, 0, SEEK_CUR);
       
      write(data_fd, title, sizeof(char) * (strlen(title) + 1));
      
      current_article++;
      current_article->article_id = page_id;
      current_article->title_offset = offset;
      
      current_article->outgoing_links = 0;
      current_article->incoming_links = 0;
      current_article->outgoing_offset = 0;
      current_article->incoming_offset = 0;
    }
    
    return 0;
  } else if (action == ACTION_LINK) {
    
    uint32_t from = 0, to = 0;
    uint32_t * links = malloc(sizeof(uint32_t) * 1024);
    uint32_t num_links = 0;
    uint32_t last_article_id = 0;
    
    while (fscanf(input_file, "%d %d", &from, &to) != EOF) {
      if (from != last_article_id) {
        if (last_article_id != 0) {
          uint32_t offset = lseek(data_fd, 0, SEEK_CUR);
          
          write(data_fd, links, sizeof(uint32_t) * num_links);
          
          while ((++current_article)->article_id < from);
 
          if (!incoming) {
            current_article->outgoing_links = num_links;
            current_article->outgoing_offset = offset;
          } else {
            current_article->incoming_links = num_links;
            current_article->incoming_offset = offset;
          }
          
          num_links = 0;
        }
         
        last_article_id = from;
      };
      
      if (num_links + 1 >= links_capacity) {
        links_capacity <<= 1;
        links = realloc(links, sizeof(int) * links_capacity);
      };
      
      num_links++;
      links[num_links] = (uint32_t)to;
    };
    
    if (last_article_id != 0) {
      uint32_t offset = lseek(data_fd, 0, SEEK_CUR);
      
      write(data_fd, links, sizeof(uint32_t) * num_links);
      
      if (!incoming) {
        current_article->outgoing_links = num_links;
        current_article->outgoing_offset = offset;
      } else {
        current_article->incoming_links = num_links;
        current_article->incoming_offset = offset;
      }
    }
    
  } else if (action == ACTION_STATS) {
    
    uint32_t i;
    uint32_t has_title, has_id, has_incoming, has_outgoing, has_anything;
    uint32_t incoming_links, outgoing_links;
    uint32_t size_distribution[1024];
    
    memset(size_distribution, '\0', sizeof(uint32_t) * 1024);
      
    for (i = 0; i < MAX_NUMBER_OF_ARTICLES; i++) {
      article * art = &articles[i];
      
      if (art->article_id != 0 || art->incoming_links != 0 ||
          art->outgoing_links != 0 || art->title_offset != 0) {
        has_anything++;
      }
      
      if (art->article_id != 0)
        has_id++;
      if (art->incoming_links != 0)
        has_incoming++;
      if (art->outgoing_links != 0)
        has_outgoing++;
      if (art->title_offset != 0)
        has_title++;
      
      if (art->outgoing_links < 1024 && art->article_id != 0)
        size_distribution[art->outgoing_links]++;
      
      incoming_links += art->incoming_links;
      outgoing_links += art->outgoing_links;
    }
    
    printf("# Global Counters\n");
    printf("max_articles:   %12i\n", MAX_NUMBER_OF_ARTICLES);
    printf("total_articles: %12i (%0.1f%%)\n", has_anything, has_anything * 100.0 / MAX_NUMBER_OF_ARTICLES);
    printf("w/title:        %12i (%0.1f%%)\n", has_title, has_title * 100.0 / has_anything);
    printf("w/id:           %12i (%0.1f%%)\n", has_id, has_id * 100.0 / has_anything);
    printf("w/incoming:     %12i (%0.1f%%)\n", has_incoming, has_incoming * 100.0 / has_anything);
    printf("w/outgoing:     %12i (%0.1f%%)\n", has_outgoing, has_outgoing * 100.0 / has_anything);
    printf("\n");
    printf("# Statistics:\n");
    printf("incoming_links: %12i\n", incoming_links);
    printf("outgoing_links: %12i\n", outgoing_links);
    printf("\n");
    printf("# Averages:\n");
    printf("ilinks_per_pg:  %0.2f\n", (float)incoming_links / has_anything);
    printf("olinks_per_pg:  %0.2f\n", (float)outgoing_links / has_anything);
    printf("\n");
    printf("# Outgoing Link Count Distribution:\n");
    
    for (i = 0; i < 1024; i++)
      printf("ol=%-12i %12i\n", i, size_distribution[i]);
    
  } else if (action == ACTION_SIMULATION) {
    printf("# Not implemented...\n");
  }
  
  
  munmap(articles, 1 << 24);
  
  close(index_fd);
  close(data_fd);
};
