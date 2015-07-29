#!/usr/bin/env Rscript

#-----------------
# Load libraries
#-----------------
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(magrittr))
suppressPackageStartupMessages(library(tidyr))
suppressPackageStartupMessages(library(lubridate))
suppressPackageStartupMessages(library(readr))


#----------------------
# Load and clean data
#----------------------
cat("Loading raw data (will take a while)...\n")
city.data <- read_csv("data/city_data_raw_final.zip", col_types="iDcd") %>%
  rename(ni_date = date) %>%
  mutate(ni_year = year(ni_date),
         ni_month = month(ni_date),
         ni_week = week(ni_date),
         ni_mday = day(ni_date),
         ni_yday = yday(ni_date))
cat("Done.\n")

cities <- read_csv("data/cities_final.csv", col_types="iccdd") %>%
  rename(city_name = name)

stat.cols <- c("dl_broadband", "ul_broadband", "quality", 
               "promise", "value", "ul_mobile", "dl_mobile")

cat("\nConverting raw data to wide (will take a while)...")
city.data.wide <- city.data %>% 
  # head(100000) %>%
  spread(stat, value)
cat(" done.\n")


#------------------------------------------------------------------------
# Get daily, weekly, monthly, and yearly averages for cities and states
#------------------------------------------------------------------------
cat("\nSummarizing yearly city data...")
data.city.yearly <- city.data.wide %>%
  group_by(net_index_id, ni_year) %>%
  summarise_each(funs(mean(., na.rm=TRUE)), one_of(stat.cols)) %>%
  left_join(cities, by="net_index_id") %>%
  select(net_index_id, city_name:longitude, ni_year:quality) %T>%
  write_csv("data/city_yearly.csv")
cat(" done.\n")

cat("Summarizing monthly city data...")
data.city.monthly <- city.data.wide %>%
  group_by(net_index_id, ni_year, ni_month) %>%
  summarise_each(funs(mean(., na.rm=TRUE)), one_of(stat.cols)) %>%
  left_join(cities, by="net_index_id") %>%
  select(net_index_id, city_name:longitude, ni_year:quality) %T>%
  write_csv("data/city_monthly.csv")
cat(" done.\n")

cat("Summarizing weekly city data...")
data.city.weekly <- city.data.wide %>%
  group_by(net_index_id, ni_year, ni_week) %>%
  summarise_each(funs(mean(., na.rm=TRUE)), one_of(stat.cols)) %>%
  left_join(cities, by="net_index_id") %>%
  select(net_index_id, city_name:longitude, ni_year:quality) %T>%
  write_csv("data/city_weekly.csv")
cat(" done.\n")

cat("Summarizing daily city data (will take a while)...")
data.city.daily <- city.data.wide %>%
  left_join(cities, by="net_index_id") %>%
  select(net_index_id, city_name:longitude, ni_date:ni_yday, one_of(stat.cols)) %T>%
  write_csv("data/city_daily.csv")
cat(" done.\n")

cat("\nSummarizing yearly state data...")
data.state.yearly <- city.data.wide %>%
  left_join(cities, by="net_index_id") %>%
  group_by(state, ni_year) %>%
  summarise_each(funs(mean(., na.rm=TRUE)), one_of(stat.cols)) %T>%
  write_csv("data/state_yearly.csv")
cat(" done.\n")

cat("Summarizing monthly state data...")
data.state.monthly <- city.data.wide %>%
  left_join(cities, by="net_index_id") %>%
  group_by(state, ni_year, ni_month) %>%
  summarise_each(funs(mean(., na.rm=TRUE)), one_of(stat.cols)) %T>%
  write_csv("data/state_monthly.csv")
cat(" done.\n")

cat("Summarizing weekly state data...")
data.state.weekly <- city.data.wide %>%
  left_join(cities, by="net_index_id") %>%
  group_by(state, ni_year, ni_week) %>%
  summarise_each(funs(mean(., na.rm=TRUE)), one_of(stat.cols)) %T>%
  write_csv("data/state_weekly.csv")
cat(" done.\n")

cat("Summarizing daily state data...")
data.state.daily <- city.data.wide %>%
  left_join(cities, by="net_index_id") %>%
  group_by(state, ni_date) %>%
  summarise_each(funs(mean(., na.rm=TRUE)), one_of(stat.cols)) %T>%
  write_csv("data/state_daily.csv")
cat(" done.\n")

cat("\nAll done! \\(•◡•)/\n")
