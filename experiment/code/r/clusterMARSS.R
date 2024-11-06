#install.packages("tidyverse", "janitor", "lubridate", "MARSS")
library(tidyverse)
library(janitor)
library(lubridate)
library(MARSS)

body_size <- read_csv("body_size.csv")

#Load count data
alive <- read_csv("mortality.csv") %>% 
  clean_names() %>%
  mutate(date = if_else(mdy(date) == ymd("2024-01-31"), mdy(date)-days(1), mdy(date))) #correct for date

#Load behavior data
open <- read_csv("behavior.csv") %>% 
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

#Load temperature data
weekly_temp <- read_csv("weekly_temperature.csv")

############################################ Tidy data

start_date <- min(weekly_temp$friday)

all_size_marss <- all %>%
  filter(!is.na(avg_size)) %>%
  mutate(week = as.numeric(difftime(date, start_date, units = "weeks")) + 1,
         avg_size_log = log(avg_size),
         sd_size_log = log(sd_size),
         tank = as.numeric(tank)) %>%
  select(date, week, tank, mhw, genet, avg_size_log) %>%
  left_join(weekly_temp, by = c("date" = "friday", "tank"))

marss_data <- all_size_marss %>%
  mutate(genet_tank = paste(genet, tank, sep = "_"))

marss_data_wide <- marss_data %>%
  select(-date, -tank, -genet, -mhw, -treatment, -avg_temp, -min_temp, -max_temp) %>%
  pivot_wider(names_from = genet_tank, values_from = avg_size_log) %>%
  column_to_rownames(var = "week") %>%
  as.matrix() %>%
  t()

genotype_vec <- rep(c("A", "B", "C", "D", "E"), times = 15)
genotype_numeric <- as.numeric(factor(genotype_vec, levels = c("A", "B", "C", "D", "E")))
A_matrix <- matrix(genotype_numeric, ncol=1)

temp_cov <- weekly_temp %>%
  filter(friday < ymd("2024-02-16")) %>%
  arrange(friday, tank) %>%
  slice(rep(1:n(), each = 5)) %>%
  mutate(tank_rep = paste0(tank, letters[1:5][rep(1:5, times = n()/5)])) %>%
  select(tank_rep, friday, avg_temp) %>%
  pivot_wider(names_from = tank_rep, values_from = avg_temp) %>%
  mutate(week = row_number()) %>%
  select(-friday) %>%
  column_to_rownames(var = "week") %>%
  as.matrix() %>%
  t()

# Make blank temperature covariate interaction matrix
C_matrix <- matrix(0, nrow = 75, ncol = 75)
#Fill in interaction matrix
for (tank in 1:15) {
  start_row <- (tank - 1) * 5 + 1
  end_row <- start_row + 4  # 5 genotypes per tank
  for (i in start_row:end_row) {
    for (j in start_row:end_row) {
      C_matrix[i, j] <- tank
    }
  }
}

############################### MARSS

model_listQ1 <- list(
  B = "diagonal and unequal",
  U = "unequal",
  Q = "diagonal and equal",
  Z = "identity",
  A = A_matrix,
  R = "identity",
  C = C_matrix,
  c = temp_cov
)

kemfitQ1 <- MARSS(y = marss_data_wide, model = model_listQ1,
                  control = list(maxit= 100, allow.degen=TRUE, trace=1, safe=TRUE), fit=TRUE)
fitQ1 <- MARSS(y = marss_data_wide, model = model_listQ1,
               control = list(maxit = 5000), inits=kemfitQ1$par)