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

temp_covariate <- weekly_temp %>%
  filter(friday < ymd("2024-02-16")) %>%
  arrange(friday, tank) %>%
  select(tank, friday, avg_temp) %>%
  pivot_wider(names_from = tank, values_from = avg_temp) %>%
  mutate(week = row_number()) %>%
  select(-friday) %>%
  column_to_rownames(var = "week") %>%
  as.matrix() %>%
  t()

C_matrix <- matrix(factor(paste("tank", rep(1:15, each = 1), sep = "")), ncol = 1)

Z_models <- list(
  H1 = matrix(factor(rep(1, 75))),
  H2 = matrix(factor(c(rep("amb", 25), rep("sev", 25), rep("ext", 25)))),
  H3 = matrix(factor(rep(c("A", "B", "C", "D", "E"), 15))),
  H4 = matrix(factor(c(rep("amb", 25), rep("mhw", 50)))),
  H5 = matrix(factor(c(rep("amb", 25), rep("sev", 25), rep("amb", 25)))), # post-hoc hypothesis
  H6 = matrix(factor(rep(c("gen1", "gen2", "gen2", "gen2", "gen1"), 15))), # post-hoc hypothesis
  H7 = matrix(factor(rep(c("gen1", "gen2", "gen3", "gen4", "gen1"), 15))), # post-hoc hypothesis
  H8 = matrix(factor(c(rep(c("amb_gen1", "amb_gen2", "amb_gen2", "amb_gen2", "amb_gen1"), 5),
                       rep(c("sev_gen1", "sev_gen2", "sev_gen2", "sev_gen2", "sev_gen1"),5),
                       rep(c("amb_gen1", "amb_gen2", "amb_gen2", "amb_gen2", "amb_gen1"), 5)))))
  #H10 = matrix(factor(rep(c("heatwave", "recovery"), each = 12)))) # post-hoc hypothesis
#H9 = matrix(factor(1:75)) #Do not use! Overfits the data and has by far the worst AIC 

names(Z_models) <- c("all_same", "diff_treat", "diff_genet", "mhw_same", "amb_ext_same", "AE_BCD", "AE_B_C_D", "ambExt_AE_BCD") #, "all_diff")

############################### MARSS

mod_list <- list(
  B = "diagonal and equal",
  U = "unequal",
  Q = "diagonal and equal",
  Z = "placeholder",
  A = "zero",
  R = "diagonal and equal",
  C = C_matrix,
  c = temp_covariate
)

out.tab <- NULL
fits <- list()

for (i in 1:length(Z_models)) {
  mod_list$Z <- Z_models[[i]]
  fit <- MARSS(y=marss_data, model = mod_list, silent = TRUE, 
               control = list(maxit = 5000))
  out <- data.frame(H = names(Z_models)[i], logLik = fit$logLik, 
                    AICc = fit$AICc, num.param = fit$num.params, m = length(unique(Z_models[[i]])), 
                    num.iter = fit$numIter, converged = !fit$convergence)
  out.tab <- rbind(out.tab, out)
  fits <- c(fits, list(fit))
}

print(out.tab) #looking for: higher log likelihood, lower AIC

for (i in 1:length(fits)) {
  par(mfrow = c(2, 3))
  resids <- MARSSresiduals(fits[[i]], type = "tt1")
  for (j in 1:15) {
    plot(resids$model.residuals[j, ], ylab = "model residuals", 
         xlab = "")
    abline(h = 0)
    title(paste(names(Z_models[i]), ":", rownames(marss_data)[j]))
  }
}