# cartoframes Analysis Service

## Getting set up

```bash
$ git clone https://github.com/andy-esch/flask-cartoframes-app.git
$ cd flask-cartoframes-app
$ pip install -r requirements.txt
$ python analysis_service.py
```

This will point to `http://localhost:5000` which has the following endpoints:

* [`/`](#identity-) - will display the data in `table`
* [`/kmeans`](#kmeans) - will do a naive k-means analysis of `cols` in `table`
* [`/udf`](#udf) - user-defined Python function

## End Points

### kmeans

**End point:** `/kmeans`

**Params**

* `user` - CARTO username
* `key` - CARTO API Key
* `table` - name of table to display
* `n_clusters` - number of clusters in the analysis
* `cols` - comma-separated list of columns

**Example:**

```
http://127.0.0.1:5000/kmeans?n_clusters=7&cols=mag,depth&table=all_month_3&user=eschbacher&key=abcdefg
```

The result of this analysis is a new table written to the user's CARTO account with the results of the analysis.

### udf 

**End point:** `/udf`

**Params**

* `user` - CARTO username
* `key` - CARTO API Key
* `table` - source table
* `col` - column to do the analysis on
* `udf` - Python script to run

The `udf` script needs to take into account that it will be operating on a DataFrame of `table`, so all the local variables will be available in the `udf` script. The outputs should be appended to the existing `df` DataFrame as new column names. The augmented DataFrame is then written to the CARTO account, and the new name is reported in the API response.

**Example**

```
http://127.0.0.1:5000/udf?table=sim_pickups&user=eschbacher&key=abcdefg&col=n_pickups&udf=import%20numpy%20as%20np;%20np.random.seed();%20mean_val%20=%20df[col];%20df[%27sim_col%27]%20=%20np.random.poisson(mean_val,%20len(df))
```

The result of this analysis is a new table written to the user's CARTO account with the results of the analysis.
### identity (`/`)

**End point:** `/`

**Params**

* `user` - CARTO username
* `key` - CARTO API Key
* `table` - name of table to display

**Example:**

```
http://127.0.0.1:5000/?table=sim_pickups&user=eschbacher&key=abcdefg
```

JSON representation of the data in that table will be returned.
