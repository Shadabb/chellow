import sys
import os
from net.sf.chellow.monad import Monad
import StringIO
import g_bill_import
import db
import templater
import utils
Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'g_bill_import')
inv, template = globals()['inv'], globals()['template']

GContract, Contract = db.GContract, db.Contract


def make_fields(sess, g_batch, message=None):
    messages = [] if message is None else [str(message)]
    parser_names = ', '.join(
        '.' + row[0][14:] for row in sess.query(Contract.name).filter(
            Contract.name.like("g_bill_parser_%")))
    return {
        'messages': messages,
        'importer_ids': sorted(
            g_bill_import.get_bill_importer_ids(g_batch.id), reverse=True),
        'g_batch': g_batch, 'parser_names': parser_names}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        g_batch_id = inv.getLong('g_batch_id')
        g_batch = db.GBatch.get_by_id(sess, g_batch_id)
        templater.render(inv, template, make_fields(sess, g_batch))
    else:
        g_batch_id = inv.getLong('g_batch_id')
        g_batch = db.GBatch.get_by_id(sess, g_batch_id)
        file_item = inv.getFileItem("import_file")
        f = StringIO.StringIO()
        if sys.platform.startswith('java'):
            from java.io import InputStreamReader

            stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
            bt = stream.read()
            while bt != -1:
                f.write(unichr(bt))
                bt = stream.read()
            file_size = file_item.getSize()
        else:
            f.writelines(file_item.f.stream)
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
        f.seek(0)
        id = g_bill_import.start_bill_importer(
            sess, g_batch.id, file_item.getName(), file_size, f)
        inv.sendSeeOther("/reports/433/output/?importer_id=" + str(id))
except utils.UserException, e:
    templater.render(inv, template, make_fields(sess, g_batch, e), 400)
finally:
    if sess is not None:
        sess.close()
