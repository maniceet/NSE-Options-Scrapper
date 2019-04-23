

# NSE Options Scrapper

The python script will enable you to download Options data for all derivative stocks on NSE.
It checks the present underlying value and for a call option gets the Last Traded price of the Strike Price higher than Underlying Value

## Updates
Dependencies on csv files has been removed, the script downloads csv online while it is running and gets the stocsk and lot sizes automatically. Dependency on nsepy package has also been removed.

## Getting Started

Just run the Script NSEScrapper.py on your terminal and the output csv will be generated.

### Prerequisites

Anaconda is preferred, however requirements.txt file is there in the git repo


### Installing

Install anaconda and use python 3.x version

```
conda create --name <myenv>

source activate <myenv>

pip install -r requirements.txt

```
### Running the script

Open terminal or command line, navigate to the folder where the files are and run

```
python3 NSEScrapper.py

```


## Authors

* **Maniceet Sahay** 



## Acknowledgments

* The script was written using Beautiful soup and on NSEPY. For more details on [NSEPY](https://github.com/swapniljariwala/nsepy)


