# Beijing Multi-Site Air-Quality Data (two stations)

Hourly air pollutants and weather at two of the twelve monitoring stations of the data set, 1 March 2013 to 28 February 2017 (35,064 rows each):

| File | Station |
|---|---|
| `PRSA_Data_Dongsi_20130301-20170228.csv` | Dongsi (urban, central Beijing) |
| `PRSA_Data_Dingling_20130301-20170228.csv` | Dingling (rural, northwest of the city) |

The files are copied **unmodified** from the UCI zip (`PRSA2017_Data_20130301-20170228.zip`), which cannot be read by a browser directly. Missing values are `NA`, as in the source.

Columns: `No, year, month, day, hour, PM2.5, PM10, SO2, NO2, CO, O3` (µg/m³), `TEMP` (°C), `PRES` (hPa), `DEWP` (°C), `RAIN` (mm), `wd` (wind direction), `WSPM` (wind speed, m/s), `station`. Times are Beijing local time (UTC+8).

## Source and license

- S. Chen. *Beijing Multi-Site Air Quality* [Dataset]. UCI Machine Learning Repository, 2017. https://doi.org/10.24432/C5RK5G
- S. Zhang, B. Guo, A. Dong, J. He, Z. Xu, S. X. Chen. Cautionary tales on air-quality improvement in Beijing. *Proceedings of the Royal Society A* 473(2205): 20170457, 2017. https://doi.org/10.1098/rspa.2017.0457

License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
