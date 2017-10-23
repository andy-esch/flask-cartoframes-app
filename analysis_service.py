from flask import Flask, request
import cartoframes
import json

app = Flask(__name__)


@app.route("/", methods=['GET'])
def identity():
    """displays data in `table` as a JSON response"""
    username = request.args.get('user')
    key = request.args.get('key')
    table = request.args.get('table')
    limit = request.args.get('limit', 10)
    if not all((username, key, table)):
        return json.dumps(
            {'error': 'Key, table, and username all need to be specified'})
    cc = cartoframes.CartoContext(
            base_url='https://{}.carto.com/'.format(username),
            api_key=key)

    df = cc.read(table, limit=limit)
    return df.to_json()


@app.route("/udf", methods=['GET'])
def udf():
    """User-defined function
    Needs more work on functional form.
    It currently only takes a table and column name for processing.
    """
    func = request.args.get('udf')
    user = request.args.get('user')
    key = request.args.get('key')
    table = request.args.get('table')
    # col is used within the user-defined function
    col = request.args.get('col') # noqa: variable used in user-defined script
    if not func:
        return json.dumps({
            'result': {
                'error': 'User-defined function not specified'
                }
            })
    cc = cartoframes.CartoContext(base_url='https://{}.carto.com'.format(user),
                                  api_key=key)
    df = cc.read(table)
    # dangerous
    exec(func)
    out_table = table + '_analysis_service_output_udf'
    cc.write(df, out_table, overwrite=True)
    out_url = cc.creds.base_url() + '/' + out_table
    return json.dumps({
                'result': {
                    'success': 'Results written to {}'.format(out_url)
                }
            })


@app.route("/kmeans", methods=['GET'])
def kmeans():
    """k-means analysis

    Params:
        cols (str): Comma-separated list of columns in `table`.
        table (str): Name of table for data with columns `cols`.
        n_clusters (int): Number of clusters for the analysis. Defaults to 5.
        user (str): Username for CARTO account.
        key (str): User's CARTO API Key
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    n_clusters = int(request.args.get('n_clusters', 5))
    cols = request.args.get('cols').split(',')
    table = request.args.get('table')
    user = request.args.get('user')
    key = request.args.get('key')

    if not all((cols, table, user, key)):
        return json.dumps({'result': 'error'})

    cc = cartoframes.CartoContext(
            base_url='https://{}.carto.com/'.format(user),
            api_key=key)
    # gather the data
    df = cc.query('''
        SELECT *
          FROM {table}
    '''.format(table=table))
    scaler = StandardScaler()
    data = scaler.fit_transform(df[cols].values)
    km = KMeans(n_clusters=n_clusters).fit(data)
    df['labels'] = km.labels_
    out_table = table + '_flask_app_output'
    cc.write(df, out_table, overwrite=True)
    return json.dumps({'result': {'success': 'Table written to ' + out_table}})


if __name__ == "__main__":
    app.run()
