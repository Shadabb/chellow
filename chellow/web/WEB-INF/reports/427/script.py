from net.sf.chellow.monad import Monad
import collections
import db
import templater
import json
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
GRegisterRead, GBill = db.GRegisterRead, db.GBill
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    g_bill_id = inv.getLong('g_bill_id')
    g_bill = GBill.get_by_id(sess, g_bill_id)
    g_reads = sess.query(GRegisterRead).filter(
        GRegisterRead.g_bill == g_bill).order_by(
        GRegisterRead.pres_date.desc())
    fields = {'g_bill': g_bill, 'g_reads': g_reads}
    try:
        breakdown = json.loads(g_bill.breakdown)

        raw_lines = g_bill.raw_lines

        rows = set()
        columns = set()
        grid = collections.defaultdict(dict)

        for k, v in breakdown.iteritems():
            if k.endswith('-gbp'):
                columns.add('gbp')
                row_name = k[:-4]
                rows.add(row_name)
                grid[row_name]['gbp'] = v
                del breakdown[k]

        for k, v in breakdown.iteritems():
            for row_name in sorted(list(rows), key=len, reverse=True):
                if k.startswith(row_name + '-'):
                    col_name = k[len(row_name) + 1:]
                    columns.add(col_name)
                    grid[row_name][col_name] = v
                    del breakdown[k]
                    break

        for k, v in breakdown.iteritems():
            pair = k.split('-')
            row_name = '-'.join(pair[:-1])
            column_name = pair[-1]
            rows.add(row_name)
            columns.add(column_name)
            grid[row_name][column_name] = v

        column_list = sorted(list(columns))
        for rate_name in [col for col in column_list if col.endswith('rate')]:
            column_list.remove(rate_name)
            column_list.append(rate_name)

        if 'gbp' in column_list:
            column_list.remove('gbp')
            column_list.append('gbp')

        row_list = sorted(list(rows))
        fields.update(
            {
                'raw_lines': raw_lines, 'row_list': row_list,
                'column_list': column_list, 'grid': grid})
    except SyntaxError, e:
        pass
    render(inv, template, fields)
finally:
    if sess is not None:
        sess.close()
