# Net Index Parser

[![Python 3.4 or greater](https://img.shields.io/badge/python-%3E3.4-0074D9.svg?style=flat-square)]()
[![R 3.2 or greater](https://img.shields.io/badge/r-%3E3.2-0074D9.svg?style=flat-square)]()
[![MIT License](https://img.shields.io/badge/license-MIT%20License-2ECC40.svg?style=flat-square)](https://github.com/andrewheiss/Net-Index/blob/master/LICENSE.md)

Access the undocumented API for Ookla's fantastic [Net Index](http://www.netindex.com), convert the resulting JSON to CSV, and munge the resulting CSV with R.


## Installation

Because it can take a while to make all the necessary API calls (each city requires 7 individual API calls), it's best to run this script on a separate computer, preferrably a virtual machine in the cloud, like a [Digital Ocean server](https://www.digitalocean.com) or [Amazon EC2 instance](http://aws.amazon.com/ec2/). 

1. Install [Python 3](https://www.python.org) and [R 3](http://www.r-project.org) (script last tested with Python 3.4.3 and R 3.2.1)
    * Python
        * Ubuntu: Python 3 is preinstalled in Ubuntu 12.10 and above as `python3`
        * OS X: Install Python 3 using [Homebrew](http://brew.sh): `brew install python3`
    * R
        * Ubuntu: [Follow these instructions](https://cran.r-project.org/bin/linux/ubuntu/README)
        * OS X: Download the [convenient binary package installer](https://cran.rstudio.com/bin/macosx/)
2. Navigate to the project folder in a terminal: `cd /path/to/netindex/`
3. Install all Python packages: `pip3 install -r requirements.txt`
4. Install all R packages: `Rscript requirements.R`


## Usage

Run the following series of commands to 

1. Navigate to the project folder in a terminal: `cd /path/to/netindex/`
2. Change any of the modifiable variables in `config.py` (though the defaults are all sensible, so you shouldn't have to change anything)
2. Run the Python script to loop through the API: `python3 netindex.py`
    * **NB**: **Running this command will take a very long time**. Each city requires 7 API calls, and there are over 6,000 cities. Peppering the server with so many back-to-back calls is not very nice, so to avoid stressing the Net Index server, the script pauses for a random amount of time between each city. The wait time is drawn from a normal distribution with a mean of 6 and standard deviation of 1 (set with ASDF and ASDF in `config.py`), so generally between 4–8 seconds. As a result, it will take upwards of 10 hours to collect each city: ![(6000 * 6) / 60 / 60 = 10](docs/latex-image-1.svg). Because it takes so long, *it's best to run this on another computer*. <!-- \frac{\approx 6,000 \text{ cities}~\times ~\mathcal{N}(6, 1) \text{ seconds}}{60 \times 60} = ~\approx 10 \text{ hours} -->
    * It's also recommended to **run the script in the background** so you can close the terminal window without killing the script. Either append a `&` to the command or use `screen`: `python3 netindex.py &` or `screen -dm netindex.py`.
    * The script provides detailed progress information in the log file (`netindex.log`), which you can track with `tail`: `tail -f netindex.log`, or, if running on a remote server, `ssh -t 111.111.111.111 "tail -f ~/local/netindex/netindex.log"`. End the tail with `ctrl+x` or don't use the `-t` flag.
    * The resuling CSV file will be ≈1 GB with millions of rows (one row for each statistic for each day for each city). 
3. Run the R script to clean and process the raw long data: `Rscript clean_data.R`. In just a few minutes, the scrip will genearte 8 CSVs (ranging from ≈24 KB to ≈1 GB).
4. All the generated CSVs will be in `data/*.csv`. If you're using a remote machine, download them to your local computer with `scp`.

The whole process (as well as some documentation for the API) is summarized in the flowcharts below:

![1. Get list of cities](docs/flowchart-01.png)

![2. Get statistics for each city](docs/flowchart-02.png)

![3. Convert to wide format and aggregate](docs/flowchart-03.png)


