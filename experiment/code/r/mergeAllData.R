library(tidyverse)
library(janitor)
library(here)
library(lubridate)

#Load body size data
body_size <- read_csv(here("experiment", "data", "body_size.csv"))

#Load count data
alive <- read_csv(here("experiment", "data", "mortality.csv")) %>% 
  clean_names() %>%
  mutate(date = if_else(mdy(date) == ymd("2024-01-31"), mdy(date)-days(1), mdy(date))) #correct for date

#Load behavior data
open <- read_csv(here("experiment", "data", "behavior.csv")) %>% 
  clean_names() %>%
  select(1:8) %>%
  mutate(date = mdy(date))

#Merge and tidy all the data
all <- full_join(open, alive, by=join_by(date==date, tank==tank, genet==genet)) %>%
  full_join(body_size, by=join_by(date==date, tank==tank, genet==genet)) %>%
  select(-time.y, -time.x, -n_polyps_sampler, -samplers) %>%
  filter(date >= ymd("2023-10-01")) %>%
  mutate(treatment = factor(case_when(tank < 6 ~ "cold", tank > 10 ~ "extreme", TRUE ~ "severe"),
                            levels = c("cold", "severe", "extreme")),
         tank=as.factor(tank),
         genet=as.factor(genet),
         across(open:closed,
                ~if_else(date > ymd("2023-09-30") & is.na(.),
                         n-rowSums(across(c(open, partial_open, partial_closed, closed)), na.rm=TRUE), .)),
         percent_open = (open+partial_open)/n,
         percent_closed = (closed+partial_closed)/n,
         percent_fully_open = open/n,
         mhw = factor(case_when(date < ymd("2023-12-12") ~ "during", TRUE ~ "after"),
                      levels = c("during", "after"))) %>% #create a new column mhw where if the date is before 12/12/23, it's "during", and if it's after, it's "after"
  group_by(tank, genet) %>%
  arrange(date) %>%
  mutate(removed_cum = if_else(is.na(cumsum(removed)), 0, cumsum(removed)),# generate cumulative number of polyps removed, to represent total number of polyps excluding removal
         n_true = alive+dying_dead+removed_cum+floating,
         diff_n_cont = n_true-lag(n_true, default = first(n_true)),
         growth_rate_cont = cumsum(diff_n_cont),
         total_biomass = avg_biomass_g*n_true) %>% #overwrite n value to incorporate cumulative number of removed polyps
  ungroup() %>%
  group_by(tank, genet, mhw) %>%
  arrange(date) %>%
  mutate(diff_n = n_true-lag(n_true, default = first(n_true)),
         growth_rate = cumsum(diff_n)) %>%
  ungroup() %>%
  filter(!is.na(date))