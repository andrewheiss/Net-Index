#!/usr/bin/env Rscript

required.packages <- c("dplyr", "magrittr", "tidyr", "lubridate", "readr")

# Check if any packages are already installed
packages.to.install <- required.packages[!(required.packages %in% 
                                             installed.packages()[,"Package"])]

# Install all not-yet-installed packages
if(length(packages.to.install) > 0) {
  cat("Installing", paste(packages.to.install, collapse=", "), 
      "and all dependencies...\n")
  install.packages(new.packages, dependencies=TRUE, 
                   repos="http://cran.rstudio.com/")
  cat("Done.\n")
} else {
  cat("All required packages are already installed.\n")
}
