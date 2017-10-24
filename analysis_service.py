"""cartoframes analysis service
"""
import io
import json
import base64
import warnings

from flask import Flask, request, render_template, make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns
import cartoframes

app = Flask(__name__)


@app.route("/", methods=['GET'])
def identity():
    """displays data in `table` as a JSON response"""
    username = request.args.get('user')
    key = request.args.get('key')
    table = request.args.get('table')
    limit = int(request.args.get('limit', 10))
    out_format = request.args.get('format', 'json').lower()
    if not table:
        with open('index.html', 'r') as f:
            return f.read()
    elif not all((username, key, table)):
        return json.dumps(
            {'error': 'Key, table, and username all need to be specified'})
    cc = cartoframes.CartoContext(
            base_url='https://{}.carto.com/'.format(username),
            api_key=key)

    df = cc.read(table, limit=limit)
    if out_format == 'html':
        return df.to_html()
    elif out_format == 'json':
        return df.to_json()
    else:
        return json.dumps(
                {'error': 'HTML and JSON are the only supported formats'})


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
    out_url = cc.creds.base_url() + '/dataset/' + out_table
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
    from sklearn.preprocessing import StandardScaler, Imputer
    from cartoframes import Layer
    from cartoframes.styling import bold
    n_clusters = int(request.args.get('n_clusters', 5))
    cols = request.args.get('cols').split(',')
    table = request.args.get('table')
    user = request.args.get('user')
    key = request.args.get('key')
    out_format = request.args.get('format')

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
    imp = Imputer(missing_values='NaN', strategy='mean', axis=0)
    imp.fit(df[cols].values)
    data = imp.transform(df[cols].values)
    data = scaler.fit_transform(data)
    km = KMeans(n_clusters=n_clusters).fit(data)
    df['labels'] = km.labels_
    df['labels'] = df['labels'].astype(str)
    warnings.warn(str(df.dtypes))
    out_table = table + '_flask_app_output'
    cc.write(df, out_table, overwrite=True)
    if out_format != 'html':
        return json.dumps({
            'result': {
                'success': 'Table written to ' + out_table
            }
        })
    else:
        msg = ('Performing <b>k-means</b> on columns {cols} from {table} '
               'using {n} clusters.').format(cols=', '.join(cols),
                                             table=table,
                                             n=n_clusters)
        map_html = cc.map(layers=Layer(out_table,
                                       color={'column': 'labels',
                                              'scheme': bold(n_clusters)}
                                       )
                          ).data
        table_link = '{0}/dataset/{1}'.format(cc.creds.base_url(), out_table)
        return render_template('kmeans.html',
                               map_html=map_html,
                               table=out_table,
                               table_link=table_link,
                               user=user,
                               msg=msg,
                               plot=plot(df, cols, hue='labels'))


def plot(df, cols, hue='labels'):
    pal = sns.color_palette(['#7F3C8D', '#11A579', '#3969AC', '#F2B701',
                             '#E73F74', '#80BA5A', '#E68310', '#008695',
                             '#CF1C90', '#f97b72', '#4b4b8f', '#A5AA99'])
    img = io.BytesIO()
    sns.set(style="darkgrid")
    sns.pairplot(df, vars=cols, hue=hue, palette=pal)
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return '<img src="data:image/png;base64,{}" />'.format(plot_url)


if __name__ == "__main__":
    app.run()
