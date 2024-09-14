library(tidyverse)
library(here)
library(lubridate)
library(janitor)
library(data.table)

#Remove anything in the environment, but exclude the object "all"
#rm(list=ls()[!ls() %in% "body_size"])
#remove everything in the environment
rm(list=ls())

temp_files <- list.files(here("experiment", "data", "rpi"), pattern=".*csv")
temp_all <- data.frame()
for (i in 1:length(temp_files)){
  print(temp_files[i])
  temp_data <- read_csv(here("experiment", "data", "rpi", temp_files[i])) #each file will be read in, specify which columns you need read in to avoid any error
  temp_all <- rbind(temp_all, temp_data) #for each iteration, bind the new data to the building dataset
}

temp_all <- temp_all %>%
  clean_names() %>%
  select(1:25)

if(FALSE){
  type1_files <- list.files(here("experiment", "data", "rpi", "type1"), pattern=".*csv")
  temp_1 <- data.frame()
  for (i in 1:length(type1_files)){
    print(type1_files[i])
    temp_data <- read_csv(here("experiment", "data", "rpi", "type1", type1_files[i])) #each file will be read in, specify which columns you need read in to avoid any error
    temp_1 <- rbind(temp_1, temp_data) #for each iteration, bind the new data to the building dataset
  }
  temp_1 <- temp_1 %>%
    select(1:22) %>%
    mutate(chill_heater = "NA", 
           severe_heater = "NA",
           extreme_heater = "NA") %>%
    select(1:4, 23:25, 5:22)
  
  type2_files <- list.files(here("experiment", "data", "rpi", "type2"), pattern=".*csv")
  temp_2 <- data.frame()
  for (i in 1:length(type2_files)){
    print(type2_files[i])
    temp_data <- read_csv(here("experiment", "data", "rpi", "type2", type2_files[i])) #each file will be read in, specify which columns you need read in to avoid any error
    temp_2 <- rbind(temp_2, temp_data) #for each iteration, bind the new data to the building dataset
  }
  temp_2 <- temp_2 %>%
    select(1:19) %>%
    mutate(chill_set = "0",
           severe_set = chill_set,
           extreme_set = chill_set,
           chill_heater = "NA", 
           severe_heater = "NA",
           extreme_heater = "NA") %>%
    select(1, 20:25, 2:19)
}

chill <- c("x28_00000eb5045f","x28_00000eb3fd89","x28_00000eb42add","x28_00000eb51050","x28_00000eb4cb62")
severe <- c("x28_00000eb50e10","x28_00000eb501b0", "x28_00000eb496d2", "x28_00000eb3cf7d", "x28_00000eb52c32")
extreme <- c("x28_00000ec23ab6","x28_00000ec25534","x28_00000eb4b7e0", "x28_00000ec24f93", "x28_00000eb4619b")


sensors <- c("x28_00000eb5045f","x28_00000eb3fd89","x28_00000eb42add","x28_00000eb51050","x28_00000eb4cb62", "x28_00000eb50e10","x28_00000eb501b0", "x28_00000eb496d2", "x28_00000eb3cf7d", "x28_00000eb52c32", "x28_00000ec23ab6","x28_00000ec25534","x28_00000eb4b7e0", "x28_00000ec24f93", "x28_00000eb4619b")
#sensors <- c("x28_00000eb42add", "x28_00000ec23ab6", "x28_00000eb50e10", "x28_00000eb5045f", "x28_00000eb4a798", "x28_00000eb4cb62", "x28_00000eb51050", "x28_00000ec25534", "x28_00000eb501b0", "x28_00000eb496d2", "x28_00000eb4b7e0", "x28_00000eb3fd89", "x28_00000ec24f93", "x28_00000eb3cf7d", "x28_00000eb3f54e", "x28_00000eb4619b", "x28_00000eb52c32")
sensor_list <- as.data.frame(cbind(1:length(sensors), sensors))
colnames(sensor_list) <- c("tank", "sensor")

temp_clean <- temp_all %>%
  select(1:7, 8:25) %>%
  mutate(timestamp = ymd_hms(timestamp),
         severe_set = ifelse(timestamp < ymd_hms("2023-10-04 12:15:00"), chill_set, severe_set),
         extreme_set = ifelse(timestamp < ymd_hms("2023-10-04 12:15:00"), chill_set, extreme_set)) %>%
  select(-(last_col(offset=2):last_col()), #%>% #remove sump tank temps
         -(c(5:7))) %>% #%>% #remove heater status
  pivot_longer(cols=5:19, names_to = "sensor", values_to = "temperature") %>%
  filter(timestamp > ymd_hms("2023-09-21 12:00:00")) %>% #only keep data since addition of Corynactis
  #filter(timestamp > ymd_hms("2024-01-20 01:00:00"))
  mutate(treatment = case_when(
    sensor %in% chill ~ "chill",
    sensor %in% severe ~ "severe",
    sensor %in% extreme ~ "extreme",
    TRUE ~ "unknown"
  ),
  treatment = factor(treatment, levels = c("chill", "severe", "extreme"))) %>%
  full_join(sensor_list, by = "sensor")

week_id <- temp_clean %>%
  arrange(timestamp) %>%
  mutate(week = ceiling_date(timestamp, unit = "week")-days(2)) %>%
  group_by(week) %>%
  summarize(
    start_date = floor_date(min(timestamp), unit = "day")-days(1),  # Set start_date to the start of the day
    end_date = ceiling_date(max(timestamp), unit = "day")-days(1)-seconds(1)) %>%
  ungroup()

#Conditional merge temperature data with week ranges 
dt1 <- as.data.table(temp_clean)
dt2 <- as.data.table(week_id)
setorder(dt2, start_date, end_date) #sort dt1 by start_date and end_date
dt1[, week := NA_character_] # Create an empty column for the week in dt1
# Loop over each row in dt1 and find the matching week in dt2
merged_dt <- dt1[dt2, on = .(timestamp >= start_date, timestamp <= end_date), week := i.week]

find_next_weekday <- function(timestamp, desired_weekdays = c("Monday", "Wednesday", "Friday")) {
  # Extract the date part from timestamp
  date <- as.Date(timestamp)
  # Check if the given date is already a desired weekday
  if (weekdays(date) %in% desired_weekdays) {
    return(date)
  }
  # Loop through the next 7 days to find the closest desired weekday
  for (i in 1:7) {
    next_date <- date + i
    if (weekdays(next_date) %in% desired_weekdays) {
      return(next_date)
    }
  }
  return(NA)  # Return NA if no date is found (though it should always find one)
}

dt3 <- as.data.table(merged_dt)
dt3[, next_MWF := sapply(timestamp, function(x) as.Date(find_next_weekday(x)))]
dt3[, next_MWF := as.Date(next_MWF, origin = "1970-01-01")]

rpi_temp <- dt3 %>%
  mutate(last_SuTTh = next_MWF-days(1),
         temp_set = case_when(treatment == 'chill' ~ chill_set,
                              treatment == 'severe' ~ severe_set,
                              treatment == 'extreme' ~ extreme_set)) %>%
  select(timestamp, treatment, tank, sensor, temp_set, temperature, week, next_MWF, last_SuTTh)

rpi_temp_expt <- rpi_temp %>%
  filter(timestamp >= ymd_hms("2023-09-26 01:00:00") & timestamp <= ymd_hms("2024-02-14 01:00:00"))

##save rpi_temp
write.csv(rpi_temp, file = here("experiment", "data", "rpi_temp.csv"), row.names = FALSE)
#write.csv(rpi_temp_expt, file = here("experiment", "data", "rpi_temp_expt.csv"), row.names = FALSE)

#remove everything from environment except cleaned temp data
rm(list=ls()[!ls() %in% c("rpi_temp")])
