library(readxl)
library(here)
library(tidyverse)
library(janitor)

# read in .xslx files
rm(list=ls()) #start with a clean environment

pathname <- here("experiment", "data", "bodySize")
file_names <- list.files(path = pathname, 
                         full.names = F,
                         pattern='*.xlsx') #get a list of the names of the files (only .xlsx)

for (temp_name in file_names){
  print(temp_name)
  file.temp <- read_excel(paste0(pathname, "/", temp_name), trim_ws = TRUE) %>%
    select(!matches("[[:digit:]]")) %>% #remove columns that contain numbers (i.e. empty columns)
    clean_names() %>%
    fill(sampler, date_analysis, photo_name, tile_number, .direction = "down") %>% #fill in missing rows
    mutate(tile_number = as.factor(tile_number)) %>%
    #rename column containing some version of the word "flag" as "hello"
    rename(flag = contains("flag")) %>% #rename column containing some version of the word "flag" as "hello"
    select(1:10, flag)
  assign(gsub(".xlsx", "", temp_name, fixed = T), file.temp)
}

# merge all dataframes into one
all_data <- Reduce(full_join, mget(ls(pattern = "Corynactis"))) %>%
  #mutate_at(vars(contains("cm")), ~ .x * 10) %>% #convert cm to mm
  mutate(basal_disk_diameter_mm_a = coalesce(basal_disk_diameter_mm_a, basal_disk_diameter_cm_a),   #move cm over to mm column
         basal_disk_diameter_mm_b = coalesce(basal_disk_diameter_mm_b, basal_disk_diameter_cm_b), #move cm over to mm column
         basal_disk_diameter_mm_a = ifelse(sampler != "Sanjana",  basal_disk_diameter_mm_a*10, basal_disk_diameter_mm_a),
         basal_disk_diameter_mm_b = ifelse(sampler != "Sanjana", basal_disk_diameter_mm_b*10, basal_disk_diameter_mm_b)) %>%
  select(!contains("cm")) %>% #remove cm columns
  mutate_at(vars(contains("basal_disk_diameter")), ~ round(., 1)) %>% #round to nearest decimal place
  filter(!is.na(basal_disk_diameter_mm_a | basal_disk_diameter_mm_b) & basal_disk_diameter_mm_a | basal_disk_diameter_mm_b != 0) #remove NA/0 measurements

body_size <- all_data %>%
  filter(date_photo > ymd("2023-10-01"), #remove Oct 1 data - way too much variation in student measurements
         !(sampler == "Julia" & date_photo == ymd("2023-11-03")),#remove Julia's data from 11/3/2023
         !(sampler == "Lili" & grepl("sideways", flag))) %>% #remove sideways polyps from Lili's data 
  mutate(avg_diameter_mm = (basal_disk_diameter_mm_a+basal_disk_diameter_mm_b)/2,
         #treatment = factor(case_when(tank_number < 6 ~ "cold", tank_number > 10 ~ "extreme", TRUE ~ "severe"),
          #                  levels = c("cold", "severe", "extreme")),
         tank=tank_number,
         genet=as.factor(toupper(genet)),
         date=date_photo,
         #mhw = factor(case_when(date < ymd("2023-12-12") ~ "during", TRUE ~ "after"),
        #              levels = c("during", "after")),
         ww_g = 0.0975+3.02*avg_diameter_mm+1.08*avg_diameter_mm^2) %>% #calculate wet weight in grams, equation from 2019/2020 Corynactis body size measurements
  select(sampler, date, tank, genet, basal_disk_diameter_mm_a, basal_disk_diameter_mm_b, avg_diameter_mm, ww_g, flag) %>%
  filter(avg_diameter_mm > 1) %>%
  group_by(genet, tank, date) %>%
  summarize(avg_size = mean(c(basal_disk_diameter_mm_a, basal_disk_diameter_mm_b)),
            sd_size = sd(c(basal_disk_diameter_mm_a, basal_disk_diameter_mm_b)),
            avg_biomass_g = mean(ww_g),
            sd_biomass_g = sd(ww_g),
            n_polyps_sampler = n()/n_distinct(sampler),
            samplers=n_distinct(sampler)) %>%
  ungroup()

#remove everything from environment except cleaned data
rm(list=ls()[!ls() %in% "body_size"])