from sqlalchemy import (
    ForeignKey, Column, Integer, String, Boolean, DateTime, Text, Numeric, or_,
    not_, and_, Enum, null, create_engine)
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.schema import UniqueConstraint
import datetime
import pytz
import ast
import math
from sqlalchemy.sql.expression import true
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
import operator
from chellow.utils import (
    hh_after, HH, parse_mpan_core, hh_before, next_hh, prev_hh, hh_format)
import json
from dateutil.relativedelta import relativedelta
from functools import lru_cache
from werkzeug.exceptions import BadRequest, NotFound
import os.path
import sys
from hashlib import pbkdf2_hmac
from binascii import hexlify, unhexlify

config = {
    'PGUSER': 'postgres',
    'PGPASSWORD': 'postgres',
    'PGHOST': 'localhost',
    'PGDATABASE': 'chellow',
    'PGPORT': '5432'}


if 'RDS_HOSTNAME' in os.environ:
    for conf_name, rds_name in (
            ('PGDATABASE', 'RDS_DB_NAME'), ('PGUSER', 'RDS_USERNAME'),
            ('PGPASSWORD', 'RDS_PASSWORD'), ('PGHOST', 'RDS_HOSTNAME'),
            ('PGPORT', 'RDS_PORT')):
        config[conf_name] = os.environ[rds_name]

for var_name in (
        'PGUSER', 'PGPASSWORD', 'PGHOST', 'PGPORT', 'PGDATABASE',
        'CHELLOW_PORT'):
    if var_name in os.environ:
        config[var_name] = os.environ[var_name]

db_url = ''.join(
    [
        "postgresql+pg8000://", config['PGUSER'], ":", config['PGPASSWORD'],
        "@", config['PGHOST'], ":", config['PGPORT'], "/",
        config['PGDATABASE']])
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
Base = declarative_base()

CHANNEL_TYPES = ('ACTIVE', 'REACTIVE_IMP', 'REACTIVE_EXP')


def log_message(msg):
    sys.stderr.write(str(msg) + "\n")


def set_read_write(sess):
    sess.execute("rollback")
    sess.execute("set transaction isolation level serializable read write")


@lru_cache()
def get_non_core_contract_id(name):
    sess = None
    try:
        sess = Session()
        cont = sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'Z', Contract.name == name).one()
        return cont.id
    finally:
        if sess is not None:
            sess.close()


class PersistentClass():
    @classmethod
    def get_by_id(cls, sess, oid):
        obj = sess.query(cls).get(oid)
        if obj is None:
            raise NotFound(
                "There isn't a " + str(cls.__name__) + " with the id " +
                str(oid))
        return obj

    def _eq_(self, other):
        return type(other) is type(self) and other.id == self.id


class Snag(Base, PersistentClass):
    NEGATIVE = "Negative values"
    ESTIMATED = "Estimated"
    MISSING = "Missing"
    DATA_IGNORED = "Data ignored"

    @staticmethod
    def get_covered_snags(
            sess, site, channel, description, start_date, finish_date):
        query = sess.query(Snag).filter(
            Snag.channel == channel, Snag.site == site,
            Snag.description == description,
            or_(
                Snag.finish_date == null(),
                Snag.finish_date >= start_date)).order_by(Snag.start_date)
        if finish_date is not None:
            query = query.filter(Snag.start_date <= finish_date)
        return query.all()

    @staticmethod
    def insert_snag(sess, site, channel, description, start_date, finish_date):
        snag = Snag(site, channel, description, start_date, finish_date)
        sess.add(snag)
        return snag

    @staticmethod
    def add_snag(sess, site, channel, description, start_date, finish_date):
        background_start = start_date
        for snag in Snag.get_covered_snags(
                sess, site, channel, description, start_date, finish_date):
            if hh_before(background_start, snag.start_date):
                Snag.insert_snag(
                    sess, site, channel, description, background_start,
                    snag.start_date - HH)

            background_start = None if snag.finish_date is None else \
                snag.finish_date + HH

        if background_start is not None and \
                not hh_after(background_start, finish_date):
            Snag.insert_snag(
                sess, site, channel, description, background_start,
                finish_date)

        prev_snag = None
        for snag in Snag.get_covered_snags(
                sess, site, channel, description, start_date - HH,
                None if finish_date is None else finish_date + HH):
            if prev_snag is not None and \
                    (prev_snag.finish_date + HH) == snag.start_date and \
                    prev_snag.is_ignored == snag.is_ignored:
                prev_snag.update(prev_snag.start_date, snag.finish_date)
                sess.delete(snag)
            else:
                prev_snag = snag

    @staticmethod
    def remove_snag(sess, site, channel, description, start_date, finish_date):
        for snag in Snag.get_covered_snags(
                sess, site, channel, description, start_date, finish_date):
            out_left = snag.start_date < start_date
            out_right = hh_after(snag.finish_date, finish_date)
            if out_left and out_right:
                Snag.insert_snag(
                    sess, site, channel, description, finish_date + HH,
                    snag.finish_date)
                snag.finish_date = start_date - HH
            elif out_left:
                snag.finish_date = start_date - HH
            elif out_right:
                snag.start_date = finish_date + HH
            else:
                sess.delete(snag)
            sess.flush()

    __tablename__ = 'snag'
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('site.id'), index=True)
    channel_id = Column(Integer, ForeignKey('channel.id'), index=True)
    date_created = Column(DateTime(timezone=True), nullable=False, index=True)
    is_ignored = Column(Boolean, nullable=False, index=True)
    description = Column(String, nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    finish_date = Column(DateTime(timezone=True), index=True)

    def __init__(self, site, channel, description, start_date, finish_date):
        if site is None and channel is None:
            raise BadRequest("The site and channel can't both be null.")
        if site is not None and channel is not None:
            raise BadRequest("The site and channel can't both be present.")
        self.site = site
        self.channel = channel

        self.date_created = datetime.datetime.now(pytz.utc)
        self.description = description
        self.is_ignored = False
        self.update(start_date, finish_date)

    def update(self, start_date, finish_date):
        if start_date is None:
            raise BadRequest("The snag start date can't be null.")
        if hh_after(start_date, finish_date):
            raise BadRequest("Start date can't be after finish date.")
        self.start_date = start_date
        self.finish_date = finish_date


class GspGroup(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        group = sess.query(GspGroup).filter_by(code=code).first()
        if group is None:
            raise BadRequest(
                "The GSP group with code " + code + " can't be found.")
        return group

    __tablename__ = 'gsp_group'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='gsp_group')


class VoltageLevel(Base, PersistentClass):

    __tablename__ = "voltage_level"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    llfcs = relationship('Llfc', backref='voltage_level')

    def __init__(self, code, name):
        self.code = code
        self.name = name

    @staticmethod
    def get_by_code(sess, code):
        vl = sess.query(VoltageLevel).filter_by(code=code).first()
        if vl is None:
            raise BadRequest(
                "There is no voltage level with the code '" + code + "'.")
        return vl


class GeneratorType(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        gen_type = sess.query(GeneratorType).filter_by(code=code).first()
        if gen_type is None:
            raise BadRequest(
                "There's no generator type with the code '" + code + "'")
        return gen_type

    __tablename__ = 'generator_type'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='generator_type')

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Source(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        source = sess.query(Source).filter_by(code=code.strip()).first()
        if source is None:
            raise BadRequest(
                "There's no source with the code '" + code + "'")
        return source

    __tablename__ = "source"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    supplies = relationship('Supply', backref='source')

    def __init__(self, code, name):
        self.code = code
        self.name = name


class ReadType(Base, PersistentClass):

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        type = sess.query(ReadType).filter_by(code=code).first()
        if type is None:
            raise BadRequest(
                "The Read Type with code " + code + " can't be found.")
        return type

    __tablename__ = 'read_type'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Cop(Base, PersistentClass):

    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        type = sess.query(Cop).filter_by(code=code).first()
        if type is None:
            raise BadRequest(
                "The CoP with code " + code + " can't be found.")
        return type

    __tablename__ = 'cop'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    eras = relationship('Era', backref='cop')

    def __init__(self, code, description):
        self.code = code
        self.description = description


class RegisterRead(Base, PersistentClass):
    UNITS_INT = {0: 'kWh', 1: 'kVArh', 2: 'kW', 3: 'kVA'}
    UNITS_STR = {'kWh': 0, 'kVArh': 1, 'kW': 2, 'kVA': 3}

    @staticmethod
    def units_to_int(units_str):
        try:
            return RegisterRead.UNITS_STR[units_str]
        except KeyError:
            raise BadRequest(
                "The units '" + str(units_str) + " isn't recognized.")

    __tablename__ = 'register_read'
    id = Column(Integer, primary_key=True)
    bill_id = Column(
        Integer, ForeignKey('bill.id', ondelete='CASCADE'), nullable=False,
        index=True)
    msn = Column(String, nullable=False)
    mpan_str = Column(String, nullable=False)
    coefficient = Column(Numeric, nullable=False)
    units = Column(Integer, nullable=False, index=True)
    tpr_id = Column(Integer, ForeignKey('tpr.id'))
    previous_date = Column(DateTime(timezone=True), nullable=False)
    previous_value = Column(Numeric, nullable=False)
    previous_type_id = Column(Integer, ForeignKey('read_type.id'))
    previous_type = relationship(
        "ReadType", primaryjoin="ReadType.id==RegisterRead.previous_type_id")
    present_date = Column(DateTime(timezone=True), nullable=False)
    present_value = Column(Numeric, nullable=False)
    present_type_id = Column(Integer, ForeignKey('read_type.id'))
    present_type = relationship(
        "ReadType", primaryjoin="ReadType.id==RegisterRead.present_type_id")

    def __init__(
            self, bill, tpr, coefficient, units, msn, mpan_str, previous_date,
            previous_value, previous_type, present_date, present_value,
            present_type):

        self.bill = bill
        self.update(
            tpr, coefficient, units, msn, mpan_str, previous_date,
            previous_value, previous_type, present_date, present_value,
            present_type)

    def update(
            self, tpr, coefficient, units, msn, mpan_str, previous_date,
            previous_value, previous_type, present_date, present_value,
            present_type):
        if tpr is None and units == 'kWh':
            raise BadRequest(
                "If a register read is measuring kWh, there must be a TPR.")

        self.tpr = tpr
        self.coefficient = coefficient
        self.units = self.units_to_int(units)
        self.previous_date = previous_date
        self.previous_value = previous_value
        self.previous_type = previous_type
        self.present_date = present_date
        self.present_value = present_value
        self.present_type = present_type
        self.msn = msn
        self.mpan_str = mpan_str

    def delete(sess, self):
        sess.delete(self)

    def units_as_str(self):
        return self.UNITS_INT[self.units]


class Bill(Base, PersistentClass):

    __tablename__ = 'bill'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batch.id'), nullable=False)
    supply_id = Column(Integer, ForeignKey('supply.id'), nullable=False)
    issue_date = Column(DateTime(timezone=True), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    finish_date = Column(DateTime(timezone=True), nullable=False)
    net = Column(Numeric, nullable=False)
    vat = Column(Numeric, nullable=False)
    gross = Column(Numeric, nullable=False)
    account = Column(String, nullable=False)
    reference = Column(String, nullable=False)
    bill_type_id = Column(Integer, ForeignKey('bill_type.id'))
    breakdown = Column(String, nullable=False)
    kwh = Column(Numeric, nullable=False)
    reads = relationship(
        'RegisterRead', backref='bill', cascade="all, delete-orphan",
        passive_deletes=True)

    def __init__(
            self, batch, supply, account, reference, issue_date, start_date,
            finish_date, kwh, net, vat, gross, bill_type, breakdown):
        self.batch = batch
        self.supply = supply
        self.update(
            account, reference, issue_date, start_date, finish_date, kwh, net,
            vat, gross, bill_type, breakdown)

    def update(
            self, account, reference, issue_date, start_date, finish_date, kwh,
            net, vat, gross, bill_type, breakdown):
        self.reference = reference
        self.account = account
        if issue_date is None:
            raise Exception("The issue date may not be null.")

        self.issue_date = issue_date
        if start_date > finish_date:
            raise BadRequest(
                "The bill start date " + hh_format(start_date) +
                " can't be after the finish date " + hh_format(finish_date) +
                ".")

        self.start_date = start_date
        self.finish_date = finish_date
        if kwh is None:
            raise Exception("kwh can't be null.")

        self.kwh = kwh
        self.net = net
        self.vat = vat
        self.gross = gross
        if bill_type is None:
            raise Exception("Type can't be null.")

        self.bill_type = bill_type
        if isinstance(breakdown, dict):
            self.breakdown = repr(dict(breakdown))
        else:
            raise BadRequest(
                "The 'breakdown' parameter must be a mapping type.")

    def insert_read(
            self, sess, tpr, coefficient, units, msn, mpan_str, prev_date,
            prev_value, prev_type, pres_date, pres_value, pres_type):
        read = RegisterRead(
            self, tpr, coefficient, units, msn, mpan_str, prev_date,
            prev_value, prev_type, pres_date, pres_value, pres_type)
        sess.add(read)
        sess.flush()
        return read

    def delete(self, sess):
        sess.delete(self)
        sess.flush()


class BillType(Base, PersistentClass):

    @staticmethod
    def get_by_code(sess, code):
        bill_type = sess.query(BillType).filter(BillType.code == code).first()
        if bill_type is None:
            raise BadRequest(
                "The bill type with code " + code + " can't be found.")
        return bill_type

    __tablename__ = 'bill_type'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    bills = relationship('Bill', backref='bill_type')

    def __init__(self, code, description):
        self.code = code
        self.description = description


class Pc(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        code = code.strip()
        pc = sess.query(Pc).filter_by(code=code).first()
        if pc is None:
            raise BadRequest(
                "The PC with code " + code + " can't be found.")
        return pc

    __tablename__ = 'pc'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    eras = relationship('Era', backref='pc')


class Batch(Base, PersistentClass):
    __tablename__ = 'batch'
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('contract.id'), nullable=False)
    reference = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    bills = relationship('Bill', backref='batch')

    def __init__(self, sess, contract, reference, description):
        self.contract = contract
        self.update(sess, reference, description)

    def update(self, sess, reference, description):
        reference = reference.strip()
        if len(reference) == 0:
            raise BadRequest("The batch reference can't be blank.")

        self.reference = reference
        self.description = description.strip()
        try:
            sess.flush()
        except SQLAlchemyError:
            sess.rollback()
            raise BadRequest(
                "There's already a batch attached to the contract " +
                self.contract.name + " with the reference " + reference + ".")

    def delete(self, sess):
        sess.execute(
            "delete from bill where batch_id = :batch_id",
            {'batch_id': self.id})
        sess.delete(self)

    def insert_bill(
            self, sess, account, reference, issue_date, start_date,
            finish_date, kwh, net, vat, gross, bill_type, breakdown,
            supply=None):
        if supply is None:
            supply = sess.query(Supply).distinct().join(Era).filter(
                or_(
                    and_(
                        Era.imp_supplier_contract == self.contract,
                        Era.imp_supplier_account == account),
                    and_(
                        Era.exp_supplier_contract == self.contract,
                        Era.exp_supplier_account == account),
                    and_(
                        Era.mop_contract == self.contract,
                        Era.mop_account == account),
                    and_(
                        Era.hhdc_contract == self.contract,
                        Era.hhdc_account == account))).order_by(
                Supply.id).first()

        if supply is None:
            raise BadRequest(
                "Can't find an era with contract '" + self.contract.name +
                "' and account '" + account + "'.")

        bill = Bill(
            self, supply, account, reference, issue_date, start_date,
            finish_date, kwh, net, vat, gross, bill_type, breakdown)

        sess.add(bill)
        sess.flush()
        return bill


class Party(Base, PersistentClass):

    @staticmethod
    def get_by_participant_id_role_id(sess, participant_id, market_role_id):
        party = sess.query(Party).filter(
            Party.participant_id == participant_id,
            Party.market_role_id == market_role_id).first()
        if party is None:
            raise BadRequest(
                "There isn't a party with participant id " + participant_id +
                " and market role " + market_role_id)
        return party

    @staticmethod
    def get_by_participant_code_role_code(
            sess, participant_code, market_role_code):
        party = sess.query(Party).join(Participant).join(MarketRole).filter(
            Participant.code == participant_code,
            MarketRole.code == market_role_code).first()
        if party is None:
            raise BadRequest(
                "There isn't a party with participant code " +
                participant_code + " and market role code " + market_role_code)
        return party

    @staticmethod
    def get_by_participant_id_role_code(
            sess, participant_id, market_role_code):
        party = sess.query(Party).join(MarketRole).filter(
            Party.participant_id == participant_id,
            MarketRole.code == market_role_code).first()
        if party is None:
            raise BadRequest(
                "There isn't a party with participant id " +
                str(participant_id) + " and market role code " +
                market_role_code)
        return party

    @staticmethod
    def get_by_dno_code(sess, dno_code):
        dno = sess.query(Party).filter_by(dno_code=dno_code).first()
        if dno is None:
            raise BadRequest(
                "There is no DNO with the code '" + dno_code + "'.")
        return dno

    __tablename__ = 'party'
    id = Column(Integer, primary_key=True)
    market_role_id = Column(Integer, ForeignKey('market_role.id'), index=True)
    participant_id = Column(Integer, ForeignKey('participant.id'), index=True)
    name = Column(String, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    users = relationship('User', backref='party')
    dno_code = Column(String)
    contracts = relationship('Contract', back_populates='party')
    mtcs = relationship('Mtc', backref='dno')
    llfcs = relationship('Llfc', backref='dno')

    def get_llfc_by_code(self, sess, code):
        llfc = sess.query(Llfc).filter_by(dno=self, code=code).first()
        if llfc is None:
            raise BadRequest(
                "There is no LLFC with the code '" + code +
                "' associated with the DNO " + self.dno_code + ".")
        return llfc


class Contract(Base, PersistentClass):

    @staticmethod
    def get_non_core_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, 'Z', name)

    @staticmethod
    def get_hhdc_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, 'C', oid)

    @staticmethod
    def get_dno_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, 'R', oid)

    @staticmethod
    def get_dno_by_name(sess, name):
        cont = Contract.find_by_role_code_name(sess, 'R', name)
        if cont is None:
            raise BadRequest(
                "There isn't a DNO contract with the code '" + name + "'.")
        return cont

    @staticmethod
    def get_hhdc_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, 'C', name)

    @staticmethod
    def get_mop_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, 'M', oid)

    @staticmethod
    def get_mop_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, 'M', name)

    @staticmethod
    def get_supplier_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, 'X', oid)

    @staticmethod
    def get_supplier_by_name(sess, name):
        return Contract.get_by_role_code_name(sess, 'X', name)

    @staticmethod
    def get_non_core_by_id(sess, oid):
        return Contract.get_by_role_code_id(sess, 'Z', oid)

    @staticmethod
    def get_by_role_code_id(sess, role_code, oid):
        cont = Contract.find_by_role_code_id(sess, role_code, oid)
        if cont is None:
            raise NotFound(
                "There isn't a contract with the role code '" + role_code +
                "' and id '" + str(oid) + "'.")
        return cont

    @staticmethod
    def find_by_role_code_id(sess, role_code, oid):
        return sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == role_code, Contract.id == oid).first()

    @staticmethod
    def get_by_role_code_name(sess, role_code, name):
        cont = Contract.find_by_role_code_name(sess, role_code, name)
        if cont is None:
            raise BadRequest(
                "There isn't a contract with the role code '" + role_code +
                "' and name '" + name + "'.")
        return cont

    @staticmethod
    def find_by_role_code_name(sess, role_code, name):
        return sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == role_code, Contract.name == name).first()

    @staticmethod
    def insert_mop(
            sess, name, participant, charge_script, properties, start_date,
            finish_date, rate_script):
        return Contract.insert(
            sess, False, name, participant, 'M', charge_script, properties,
            start_date, finish_date, rate_script)

    @staticmethod
    def insert_non_core(
            sess, is_core, name, charge_script, properties, start_date,
            finish_date, rate_script):
        return Contract.insert(
            sess, is_core, name, Participant.get_by_code(sess, 'CALB'), 'Z',
            charge_script, properties, start_date, finish_date, rate_script)

    @staticmethod
    def insert_hhdc(
            sess, name, participant, charge_script, properties, start_date,
            finish_date, rate_script):
        return Contract.insert(
            sess, False, name, participant, 'C', charge_script, properties,
            start_date, finish_date, rate_script)

    @staticmethod
    def insert_supplier(
            sess, name, participant, charge_script, properties, start_date,
            finish_date, rate_script):
        return Contract.insert(
            sess, False, name, participant, 'X', charge_script, properties,
            start_date, finish_date, rate_script)

    @staticmethod
    def insert(
            sess, is_core, name, participant, role_code, charge_script,
            properties, start_date, finish_date, rate_script):
        party = Party.get_by_participant_id_role_code(
            sess, participant.id, role_code)
        contract = Contract(
            is_core, name, party, charge_script, properties, '{}')
        sess.add(contract)
        sess.flush()
        rscript = contract.insert_rate_script(sess, start_date, rate_script)
        contract.update_rate_script(
            sess, rscript, start_date, finish_date, rate_script)
        return contract

    __tablename__ = 'contract'
    id = Column(Integer, primary_key=True)
    is_core = Column(Boolean, nullable=False)
    name = Column(String, nullable=False)
    charge_script = Column(Text, nullable=False)
    properties = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    market_role_id = Column(Integer, ForeignKey('market_role.id'))
    __table_args__ = (UniqueConstraint('name', 'market_role_id'),)
    rate_scripts = relationship(
        "RateScript", back_populates="contract",
        primaryjoin="Contract.id==RateScript.contract_id")
    batches = relationship('Batch', backref='contract')
    supplies = relationship('Supply', backref='dno_contract')
    party_id = Column(Integer, ForeignKey('party.id'))
    party = relationship("Party", back_populates="contracts")
    start_rate_script_id = Column(Integer, ForeignKey('rate_script.id'))
    finish_rate_script_id = Column(Integer, ForeignKey('rate_script.id'))

    start_rate_script = relationship(
        "RateScript",
        primaryjoin="RateScript.id==Contract.start_rate_script_id")
    finish_rate_script = relationship(
        "RateScript",
        primaryjoin="RateScript.id==Contract.finish_rate_script_id")

    def __init__(
            self, is_core, name, party, charge_script, properties, state):
        self.market_role = party.market_role
        self.update(is_core, name, party, charge_script, properties)
        self.update_state(state)

    def update(self, is_core, name, party, charge_script, properties):
        self.is_core = is_core
        name = name.strip()
        if len(name) == 0:
            raise BadRequest("The contract name can't be blank.")
        self.name = name
        if party.market_role.id != self.market_role.id:
            raise BadRequest("""The market role of the party doesn't match
                    the market role of the contract.""")
        self.party = party
        self.update_properties(properties)
        try:
            ast.parse(charge_script)
        except SyntaxError as e:
            raise BadRequest(str(e))
        except NameError as e:
            raise BadRequest(str(e))
        self.charge_script = charge_script

    def update_state(self, state):
        self.state = str(state)

    def update_properties(self, properties):
        try:
            eval(properties, {'datetime': datetime.datetime})
        except SyntaxError as e:
            raise BadRequest(str(e))
        except NameError as e:
            raise BadRequest(str(e))
        self.properties = properties

    def update_rate_script(
            self, sess, rscript, start_date, finish_date, script):
        if rscript.contract != self:
            raise Exception("This rate script doesn't below to this contract.")

        if start_date is None:
            raise BadRequest("The start date can't be None.")

        if hh_after(start_date, finish_date):
            raise BadRequest("""The start date can't be after the finish
                    date.""")

        if len(script) > 0 and script[0] == '{':
            try:
                json.loads(script)
            except SyntaxError as e:
                raise BadRequest(str(e))
        else:
            try:
                ast.parse(script)
            except SyntaxError as e:
                raise BadRequest(str(e))
            except NameError as e:
                raise BadRequest(str(e))
        rscript.script = script

        prev_rscript = self.find_rate_script_at(sess, rscript.start_date - HH)
        if rscript.finish_date is None:
            next_rscript = None
        else:
            next_rscript = self.find_rate_script_at(
                sess, rscript.finish_date + HH)

        rscript.start_date = start_date
        rscript.finish_date = finish_date

        if prev_rscript is not None:
            if not hh_before(prev_rscript.start_date, start_date):
                raise BadRequest("""The start date must be after the start
                        date of the previous rate script.""")
            prev_rscript.finish_date = prev_hh(start_date)

        if next_rscript is not None:
            if finish_date is None:
                raise BadRequest("""The finish date must be before the
                        finish date of the next rate script.""")

            if not hh_before(finish_date, next_rscript.finish_date):
                raise BadRequest("""The finish date must be before the
                        finish date of the next rate script.""")

            next_rscript.start_date = next_hh(finish_date)

        sess.flush()
        rscripts = sess.query(RateScript).filter(
            RateScript.contract_id == self.id).order_by(
            RateScript.start_date).all()
        self.start_rate_script = rscripts[0]
        self.finish_rate_script = rscripts[-1]

        eras_before = sess.query(Era).filter(
            Era.start_date < self.start_rate_script.start_date,
            or_(
                Era.imp_supplier_contract_id == self.id,
                Era.exp_supplier_contract_id == self.id,
                Era.hhdc_contract_id == self.id,
                Era.mop_contract_id == self.id)).all()
        if len(eras_before) > 0:
            mpan_core = eras_before[0].imp_mpan_core
            if mpan_core is None:
                mpan_core = eras_before[0].exp_mpan_core
            raise BadRequest(
                "The era with MPAN core " + mpan_core +
                " exists before the start of this contract, and is " +
                "attached to this contract.")

        if self.finish_rate_script.finish_date is not None:
            eras_after = sess.query(Era).filter(
                Era.finish_date > self.finish_rate_script.finish_date,
                or_(
                    Era.imp_supplier_contract_id == self.id,
                    Era.exp_supplier_contract_id == self.id,
                    Era.hhdc_contract_id == self.id,
                    Era.mop_contract_id == self.id)).all()
            if len(eras_after) > 0:
                mpan_core = eras_after[0].imp_mpan_core
                if mpan_core is None:
                    mpan_core = eras_after[0].exp_mpan_core
                raise BadRequest(
                    "The era with MPAN core " + mpan_core +
                    " exists after the start of this contract, and is " +
                    "attached to this contract.")

    def delete(self, sess):
        self.rate_scripts[:] = []
        sess.delete(self)

    def find_rate_script_at(self, sess, date):
        return sess.query(RateScript).filter(
            RateScript.contract == self, RateScript.start_date <= date, or_(
                RateScript.finish_date == null(),
                RateScript.finish_date >= date)).first()

    def start_date(self):
        return self.start_rate_script.start_date

    def finish_date(self):
        return self.finish_rate_script.finish_date

    def delete_rate_script(self, sess, rscript):
        rscripts = sess.query(RateScript).filter(
            RateScript.contract == self).order_by(RateScript.start_date).all()

        if len(rscripts) < 2:
            raise BadRequest("You can't delete the last rate script.")
        if rscripts[0] == rscript:
            self.start_rate_script = rscripts[1]
        elif rscripts[-1] == rscript:
            self.finish_rate_script = rscripts[-2]

        sess.flush()
        sess.delete(rscript)
        sess.flush()

        if rscripts[0] == rscript:
            rscripts[1].start_date = rscript.start_date
        elif rscripts[-1] == rscript:
            rscripts[-2].finish_date = rscript.finish_date
        else:
            prev_script = self.find_rate_script_at(
                sess, prev_hh(rscript.start_date))
            prev_script.finish_date = rscript.finish_date

    def insert_rate_script(self, sess, start_date, script):
        scripts = sess.query(RateScript).filter(
            RateScript.contract_id == self.id).order_by(
            RateScript.start_date).all()
        if len(scripts) == 0:
            finish_date = None
        else:
            if hh_after(start_date, scripts[-1].finish_date):
                raise BadRequest(
                    "For the contract " + str(self.id) + " called " +
                    str(self.name) + ", the start date " + str(start_date) +
                    " is after the last rate script.")

            covered_script = self.find_rate_script_at(sess, start_date)
            if covered_script is None:
                finish_date = prev_hh(scripts[0].start_date)
            else:
                if covered_script.start_date == covered_script.finish_date:
                    raise BadRequest(
                        "The start date falls on a rate script which is only "
                        "half an hour in length, and so cannot be divided.")
                if start_date == covered_script.start_date:
                    raise BadRequest(
                        "The start date is the same as the start date of an "
                        "existing rate script.")

                finish_date = covered_script.finish_date
                covered_script.finish_date = prev_hh(start_date)
                sess.flush()

        new_script = RateScript(self, start_date, finish_date, script)
        sess.add(new_script)
        sess.flush()
        rscripts = sess.query(RateScript).filter(
            RateScript.contract == self).order_by(RateScript.start_date).all()
        self.start_rate_script = rscripts[0]
        self.finish_rate_script = rscripts[-1]
        sess.flush()
        return new_script

    def insert_batch(self, sess, reference, description):
        batch = Batch(sess, self, reference, description)
        try:
            sess.add(batch)
        except ProgrammingError:
            raise BadRequest(
                "There's already a batch with that reference.")
        return batch

    def make_properties(self):
        return eval(self.properties, {'datetime': datetime.datetime})

    def make_state(self):
        s = "{}" if self.state is None else self.state.strip()
        if len(s) == 0:
            return {}
        else:
            return eval(s)

    def get_batch(self, sess, reference):
        batch = sess.query(Batch).filter(
            Batch.contract == self, Batch.reference == reference).first()
        if batch is None:
            raise BadRequest(
                "The batch '" + reference + "' can't be found.")
        return batch


class Site(Base, PersistentClass):
    __tablename__ = 'site'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    site_eras = relationship('SiteEra', backref='site')
    snags = relationship('Snag', backref='site')

    def update(self, code, name):
        code = code.strip()
        if len(code) == 0:
            raise BadRequest("The site code can't be blank.")
        self.code = code
        self.name = name

    def __init__(self, code, name):
        self.update(code, name)

    def delete(self, sess):
        if len(self.site_eras) > 0:
            raise BadRequest(
                "This site can't be deleted while there are still eras "
                "attached to it.")

        for snag in self.snags:
            snag.delete(sess)
        sess.flush()
        sess.delete(self)
        sess.flush()

    @staticmethod
    def insert(sess, code, name):
        site = Site(code, name)
        try:
            sess.add(site)
            sess.flush()
        except ProgrammingError as e:
            if e.orig.args[2] == 'duplicate key value violates unique ' + \
                    'constraint "site_code_key"':
                raise BadRequest("There's already a site with this code.")
            else:
                raise e
        return site

    @staticmethod
    def find_by_code(sess, code):
        return sess.query(Site).filter_by(code=code).first()

    @staticmethod
    def get_by_code(sess, code):
        site = Site.find_by_code(sess, code)
        if site is None:
            raise BadRequest(
                "There isn't a site with the code " + code + ".")
        return site

    def insert_supply(
            self, sess, source, generator_type, supply_name, start_date,
            finish_date, gsp_group, mop_contract, mop_account, hhdc_contract,
            hhdc_account, msn, pc, mtc_code, cop, ssc, imp_mpan_core,
            imp_llfc_code, imp_supplier_contract, imp_supplier_account, imp_sc,
            exp_mpan_core, exp_llfc_code, exp_supplier_contract,
            exp_supplier_account, exp_sc):
        mpan_core = exp_mpan_core if imp_mpan_core is None else imp_mpan_core
        if mpan_core is None:
            raise BadRequest(
                "An era must have either an import or export MPAN core or "
                "both.")
        dno_contract = Contract.get_dno_by_name(sess, mpan_core[:2])
        supply = Supply(
            supply_name, source, generator_type, gsp_group, dno_contract)

        try:
            sess.add(supply)
            sess.flush()
        except SQLAlchemyError as e:
            sess.rollback()
            raise e

        try:
            int(mtc_code)
        except ValueError as e:
            raise BadRequest(
                "The MTC code must be a whole number. " + str(e))

        mtc = Mtc.get_by_code(sess, dno_contract.party, mtc_code)
        supply.insert_era(
            sess, self, [], start_date, finish_date, mop_contract, mop_account,
            hhdc_contract, hhdc_account, msn, pc, mtc, cop, ssc, imp_mpan_core,
            imp_llfc_code, imp_supplier_contract, imp_supplier_account, imp_sc,
            exp_mpan_core, exp_llfc_code, exp_supplier_contract,
            exp_supplier_account, exp_sc, set())
        sess.flush()
        return supply

    def hh_check(self, sess, start, finish):
        for group in self.groups(sess, start, finish, False):
            if len(group.supplies) == 1:
                continue

            hh_data = group.hh_data(sess)

            resolve_1_start = None
            resolve_1_finish = None
            snag_1_start = None
            snag_1_finish = None
            resolve_2_start = None
            resolve_2_finish = None
            snag_2_start = None
            snag_2_finish = None
            prev_start_date = None
            hh_start_date = group.start_date
            for hh in hh_data:
                if hh['exp_net'] > hh['imp_gen']:
                    if snag_1_start is None:
                        snag_1_start = hh_start_date

                    snag_1_finish = hh_start_date
                else:
                    if resolve_1_start is None:
                        resolve_1_start = hh_start_date

                    resolve_1_finish = hh_start_date

                    if snag_1_finish is not None and \
                            snag_1_finish == prev_start_date:
                        group.add_snag(
                            sess, SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
                            snag_1_start, snag_1_finish)
                        snag_1_start = None
                        snag_1_finish = None

                    if resolve_1_finish is not None and \
                            resolve_1_finish == prev_start_date:
                        group.delete_snag(
                            sess, SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
                            resolve_1_start, resolve_1_finish)
                        resolve_1_start = None
                        resolve_1_finish = None

                if hh['exp_gen'] > hh['imp_net'] + \
                        hh['imp_gen']:
                    if snag_2_start is None:
                        snag_2_start = hh_start_date

                    snag_2_finish = hh_start_date
                else:
                    if resolve_2_start is None:
                        resolve_2_start = hh_start_date

                    resolve_2_finish = hh_start_date

                    if snag_2_finish is not None and \
                            snag_2_finish == prev_start_date:
                        group.add_snag(
                            sess, SiteGroup.EXPORT_GEN_GT_IMPORT, snag_2_start,
                            snag_2_finish)
                        snag_2_start = None
                        snag_2_finish = None

                    if resolve_2_finish is not None and \
                            resolve_2_finish == prev_start_date:
                        group.delete_snag(
                            sess, SiteGroup.EXPORT_GEN_GT_IMPORT,
                            resolve_2_start, resolve_2_finish)
                        resolve_2_start = None
                        resolve_2_finish = None

                    prev_start_date = hh_start_date
                    hh_start_date = next_hh(hh_start_date)

            if snag_1_finish is not None:
                group.add_snag(
                    sess, SiteGroup.EXPORT_NET_GT_IMPORT_GEN, snag_1_start,
                    snag_1_finish)

            if resolve_1_finish is not None:
                group.delete_snag(
                    sess, SiteGroup.EXPORT_NET_GT_IMPORT_GEN, resolve_1_start,
                    resolve_1_finish)

            if snag_2_finish is not None:
                group.add_snag(
                    sess, SiteGroup.EXPORT_GEN_GT_IMPORT, snag_2_start,
                    snag_2_finish)

            if resolve_2_finish is not None:
                group.delete_snag(
                    sess, SiteGroup.EXPORT_GEN_GT_IMPORT, resolve_2_start,
                    resolve_2_finish)

    def groups(self, sess, start, finish, primary_only):
        groups = []
        check_from = start
        check_to = finish
        while check_from <= finish:
            sites = []
            supplies = []
            sites.append(self)
            if self.walk_group(sess, sites, supplies, check_from, check_to):
                sites = sorted(
                    sites, key=operator.attrgetter('_num_phys_sups', 'code'),
                    reverse=True)
                if not primary_only or sites[0] == self:
                    groups.append(
                        SiteGroup(check_from, check_to, sites, supplies))

                check_from = next_hh(check_to)
                check_to = finish
            else:
                mins = int(
                    math.floor(
                        (check_to - check_from).total_seconds() / 2 /
                        (60 * 30))) * 30
                check_to = check_from + relativedelta(minutes=mins)
        return groups

    # return true if the supply is continuously attached to the site for the
    # given period.
    def walk_group(self, sess, group_sites, group_supplies, start, finish):
        new_site = group_sites[-1]
        new_site._num_phys_sups = sess.query(SiteEra).filter(
            SiteEra.site_id == new_site.id,
            SiteEra.is_physical == true()).count()
        sups = sess.query(Supply).join(Era).join(SiteEra).filter(
            SiteEra.site == new_site, Era.start_date <= finish,
            or_(
                Era.finish_date == null(),
                Era.finish_date >= start)).distinct().all()
        num_fit = len(sess.execute(
            "select supply.id from supply, "
            "era left join "
            "(select site_era.era_id from site_era where "
            "site_era.site_id = :site_id) as sera "
            "on (era.id = sera.era_id) "
            "where era.supply_id = supply.id and "
            "era.start_date <= :finish_date and "
            "(era.finish_date is null or era.finish_date >= :start_date) "
            "group by supply.id having "
            "bool_and(sera.era_id is not null) and "
            "bool_or(era.start_date <= :start_date) and "
            "bool_or(era.finish_date is null or "
            "era.finish_date >= :finish_date)",
            {
                'site_id': new_site.id,
                'start_date': start,
                'finish_date': finish}).fetchall())

        if len(sups) == num_fit:
            for supply in sups:
                if supply not in group_supplies:
                    group_supplies.append(supply)
                    for site in sess.query(Site).join(SiteEra, Era).filter(
                            Era.supply_id == supply.id,
                            Era.start_date <= finish,
                            or_(
                                Era.finish_date == null(),
                                Era.finish_date >= start),
                            not_(
                                Site.id.in_([s.id for s in group_sites]))
                            ).distinct():
                        group_sites.append(site)
                        if not self.walk_group(
                                sess, group_sites, group_supplies, start,
                                finish):
                            return False
        else:
            return False
        return True

SALT_LENGTH = 16


class User(Base, PersistentClass):
    @staticmethod
    def insert(sess, email_address, password, user_role, party):
        try:
            user = User(email_address, password, user_role, party)
            sess.add(user)
            sess.flush()
        except ProgrammingError as e:
            if e.orig.args[2] == 'duplicate key value violates unique ' + \
                    'constraint "user_email_address_key"':
                raise BadRequest(
                    "There's already a user with this email address.")
            else:
                raise e
        return user

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email_address = Column(String, unique=True, nullable=False)
    password_digest = Column(String, nullable=False)
    user_role_id = Column(Integer, ForeignKey('user_role.id'))
    party_id = Column(Integer, ForeignKey('party.id'))

    def __init__(self, email_address, password, user_role, party):
        self.update(email_address, user_role, party)
        self.set_password(password)

    def update(self, email_address, user_role, party):
        self.email_address = email_address
        self.user_role = user_role
        if user_role.code == 'party-viewer':
            if party is None:
                raise BadRequest(
                    "There must be a party if the role is party-viewer.")
            self.party = party
        else:
            self.party = None

    def password_matches(self, password):
        digest = unhexlify(self.password_digest.encode('ascii'))
        salt = digest[:SALT_LENGTH]
        dk = digest[SALT_LENGTH:]

        return pbkdf2_hmac(
            'sha256', password.encode('utf8'), salt, 100000) == dk

    def set_password(self, password):
        salt = os.urandom(SALT_LENGTH)
        dk = pbkdf2_hmac('sha256', password.encode('utf8'), salt, 100000)
        self.password_digest = hexlify(salt + dk).decode('ascii')


class UserRole(Base, PersistentClass):
    __tablename__ = 'user_role'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    users = relationship('User', backref='user_role')

    def __init__(self, code):
        self.code = code

    @staticmethod
    def get_by_code(sess, code):
        role = sess.query(UserRole).filter_by(code=code.strip()).first()
        if role is None:
            raise BadRequest(
                "There isn't a user role with code " + code + ".")
        return role


class MarketRole(Base, PersistentClass):

    @staticmethod
    def get_by_code(sess, code):
        role = sess.query(MarketRole).filter_by(code=code).first()
        if role is None:
            raise BadRequest(
                "A role with code " + code + " cannot be found.")
        return role

    __tablename__ = 'market_role'
    id = Column(Integer, primary_key=True)
    code = Column(String(length=1), unique=True, nullable=False)
    description = Column(String, nullable=False, unique=True)
    contracts = relationship('Contract', backref='market_role')
    parties = relationship('Party', backref='market_role')


class Participant(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        participant = sess.query(Participant).filter_by(code=code).first()
        if participant is None:
            raise BadRequest(
                "There isn't a Participant with code " + code + ".")
        return participant

    __tablename__ = 'participant'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    parties = relationship('Party', backref='participant')


class RateScript(Base, PersistentClass):
    @staticmethod
    def get_by_role_code_id(sess, market_role_code, oid):
        try:
            return sess.query(RateScript).join(
                Contract.rate_scripts, MarketRole).filter(
                RateScript.id == oid,
                MarketRole.code == market_role_code).one()
        except NoResultFound:
            raise NotFound(
                "There isn't a rate script with the id " + str(oid) +
                " attached to a contract with market role code " +
                market_role_code + ".")

    @staticmethod
    def get_hhdc_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, 'C', oid)

    @staticmethod
    def get_supplier_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, 'X', oid)

    @staticmethod
    def get_non_core_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, 'Z', oid)

    @staticmethod
    def get_mop_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, 'M', oid)

    @staticmethod
    def get_dno_by_id(sess, oid):
        return RateScript.get_by_role_code_id(sess, 'R', oid)

    __tablename__ = "rate_script"
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('contract.id'))
    contract = relationship(
        "Contract", back_populates="rate_scripts",
        primaryjoin="Contract.id==RateScript.contract_id")
    start_date = Column(DateTime(timezone=True), nullable=False)
    finish_date = Column(DateTime(timezone=True), nullable=True)
    script = Column(Text, nullable=False)

    def __init__(self, contract, start_date, finish_date, script):
        self.contract = contract
        self.start_date = start_date
        self.finish_date = finish_date
        self.script = script


class Llfc(Base, PersistentClass):
    __tablename__ = 'llfc'
    id = Column(Integer, primary_key=True)
    dno_id = Column(Integer, ForeignKey('party.id'))
    code = Column(String, nullable=False)
    description = Column(String)
    voltage_level_id = Column(Integer, ForeignKey('voltage_level.id'))
    is_substation = Column(Boolean, nullable=False)
    is_import = Column(Boolean, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))


class MeterType(Base, PersistentClass):

    @staticmethod
    def get_by_code(sess, code):
        meter_type = sess.query(MeterType).filter(
            MeterType.code == code).first()
        if meter_type is None:
            raise Exception(
                "Can't find the meter type with code " + code + ".")
        return meter_type

    __tablename__ = 'meter_type'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    mtcs = relationship('Mtc', backref='meter_type')


class MeterPaymentType(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        meter_payment_type = sess.query(MeterPaymentType).filter(
            MeterPaymentType.code == code).first()
        if meter_payment_type is None:
            raise Exception(
                "Can't find the meter payment type with code " + code + ".")
        return meter_payment_type

    __tablename__ = 'meter_payment_type'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, unique=True, nullable=False)
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))
    mtcs = relationship('Mtc', backref='meter_payment_type')


class Mtc(Base, PersistentClass):
    @staticmethod
    def has_dno(code):
        num = int(code)
        return not ((num > 499 and num < 510) or (num > 799 and num < 1000))

    @staticmethod
    def find_by_code(sess, dno, code):
        dno = dno if Mtc.has_dno(code) else None
        return sess.query(Mtc).filter_by(dno=dno, code=code).first()

    @staticmethod
    def get_by_code(sess, dno, code):
        mtc = Mtc.find_by_code(sess, dno, code)
        if mtc is None:
            raise BadRequest(
                "There isn't an MTC with this code for this DNO.")
        return mtc

    __tablename__ = 'mtc'
    id = Column(Integer, primary_key=True)
    dno_id = Column(Integer, ForeignKey('party.id'), index=True)
    code = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    has_related_metering = Column(Boolean, nullable=False)
    has_comms = Column(Boolean, nullable=False)
    is_hh = Column(Boolean, nullable=False)
    meter_type_id = Column(Integer, ForeignKey('meter_type.id'))
    meter_payment_type_id = Column(
        Integer, ForeignKey('meter_payment_type.id'))
    tpr_count = Column(Integer)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    eras = relationship('Era', backref='mtc')
    __table_args__ = (UniqueConstraint('dno_id', 'code'),)


class Tpr(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        code = code.zfill(5)
        tpr = sess.query(Tpr).filter(Tpr.code == code).one()
        if tpr is None:
            raise BadRequest("The TPR code can't be found.")
        return tpr

    __tablename__ = 'tpr'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    is_teleswitch = Column(Boolean, nullable=False)
    is_gmt = Column(Boolean, nullable=False)
    clock_intervals = relationship('ClockInterval', backref='tpr')
    measurement_requirements = relationship(
        'MeasurementRequirement', backref='tpr')
    register_reads = relationship('RegisterRead', backref='tpr')


class ClockInterval(Base, PersistentClass):
    __tablename__ = 'clock_interval'
    id = Column(Integer, primary_key=True)
    tpr_id = Column(Integer, ForeignKey('tpr.id'))
    day_of_week = Column(Integer, nullable=False)
    start_day = Column(Integer, nullable=False)
    start_month = Column(Integer, nullable=False)
    end_day = Column(Integer, nullable=False)
    end_month = Column(Integer, nullable=False)
    start_hour = Column(Integer, nullable=False)
    start_minute = Column(Integer, nullable=False)
    end_hour = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False)


class MeasurementRequirement(Base, PersistentClass):
    __tablename__ = 'measurement_requirement'
    id = Column(Integer, primary_key=True)
    ssc_id = Column(Integer, ForeignKey('ssc.id'))
    tpr_id = Column(Integer, ForeignKey('tpr.id'))


class Ssc(Base, PersistentClass):
    @staticmethod
    def get_by_code(sess, code):
        code = code.zfill(4)
        ssc = sess.query(Ssc).filter_by(code=code).first()
        if ssc is None:
            raise BadRequest(
                "The SSC with code '" + code + "' can't be found.")
        return ssc

    __tablename__ = 'ssc'
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    description = Column(String)
    is_import = Column(Boolean)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    measurement_requirements = relationship(
        'MeasurementRequirement', backref='ssc')
    eras = relationship('Era', backref='ssc')


class SiteEra(Base, PersistentClass):
    __tablename__ = 'site_era'
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('site.id'))
    era_id = Column(Integer, ForeignKey('era.id'))
    is_physical = Column(Boolean, nullable=False)

    def __init__(self, site, era, is_physical):
        self.site = site
        self.era = era
        self.is_physical = is_physical


class Era(Base, PersistentClass):
    __tablename__ = "era"
    id = Column(Integer, primary_key=True)
    supply_id = Column(Integer, ForeignKey('supply.id'), nullable=False)
    site_eras = relationship('SiteEra', backref='era')
    start_date = Column(DateTime(timezone=True), nullable=False)
    finish_date = Column(DateTime(timezone=True))
    mop_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False)
    mop_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.mop_contract_id")
    mop_account = Column(String, nullable=False)
    hhdc_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False)
    hhdc_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.hhdc_contract_id")
    hhdc_account = Column(String)
    msn = Column(String)
    pc_id = Column(Integer, ForeignKey('pc.id'), nullable=False)
    mtc_id = Column(Integer, ForeignKey('mtc.id'), nullable=False)
    cop_id = Column(Integer, ForeignKey('cop.id'), nullable=False)
    ssc_id = Column(Integer, ForeignKey('ssc.id'))
    imp_mpan_core = Column(String)
    imp_llfc_id = Column(Integer, ForeignKey('llfc.id'))
    imp_llfc = relationship("Llfc", primaryjoin="Llfc.id==Era.imp_llfc_id")
    imp_supplier_contract_id = Column(Integer, ForeignKey('contract.id'))
    imp_supplier_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.imp_supplier_contract_id")
    imp_supplier_account = Column(String)
    imp_sc = Column(Integer)
    exp_mpan_core = Column(String)
    exp_llfc_id = Column(Integer, ForeignKey('llfc.id'))
    exp_llfc = relationship("Llfc", primaryjoin="Llfc.id==Era.exp_llfc_id")
    exp_supplier_contract_id = Column(Integer, ForeignKey('contract.id'))
    exp_supplier_contract = relationship(
        "Contract", primaryjoin="Contract.id==Era.exp_supplier_contract_id")
    exp_supplier_account = Column(String)
    exp_sc = Column(Integer)
    channels = relationship('Channel', backref='era')

    def __init__(
            self, sess, supply, start_date, finish_date, mop_contract,
            mop_account, hhdc_contract, hhdc_account, msn, pc, mtc_code, cop,
            ssc, imp_mpan_core, imp_llfc_code, imp_supplier_contract,
            imp_supplier_account, imp_sc, exp_mpan_core, exp_llfc_code,
            exp_supplier_contract, exp_supplier_account, exp_sc):
        self.supply = supply
        self.update(
            sess, start_date, finish_date, mop_contract, mop_account,
            hhdc_contract, hhdc_account, msn, pc, mtc_code, cop, ssc,
            imp_mpan_core, imp_llfc_code, imp_supplier_contract,
            imp_supplier_account, imp_sc, exp_mpan_core, exp_llfc_code,
            exp_supplier_contract, exp_supplier_account, exp_sc)

    def attach_site(self, sess, site, is_location=False):
        if site in sess.query(Site).join(SiteEra).filter(
                SiteEra.era == self).all():
            raise BadRequest(
                "The site is already attached to this supply.")

        site_era = SiteEra(site, self, False)
        sess.add(site_era)
        sess.flush()
        if is_location:
            self.set_physical_location(sess, site)

    def detach_site(self, sess, site):
        site_era = sess.query(SiteEra).filter(
            SiteEra.era == self, SiteEra.site == site).first()
        if site_era is None:
            raise BadRequest(
                "Can't detach this era from this site, as it isn't attached.")
        if site_era.is_physical:
            raise BadRequest(
                "You can't detach an era from the site where it is "
                "physically located.")

        sess.delete(site_era)
        sess.flush()

    def find_channel(self, sess, imp_related, channel_type):
        return sess.query(Channel).filter(
            Channel.era == self, Channel.imp_related == imp_related,
            Channel.channel_type == channel_type).first()

    def get_channel(self, sess, imp_related, channel_type):
        chan = self.find_channel(sess, imp_related, channel_type)
        if chan is None:
            return BadRequest("Can't find the channel.")
        return chan

    def update_dates(self, sess, start_date, finish_date):
        self.update(
            sess, start_date, finish_date, self.mop_contract, self.mop_account,
            self.hhdc_contract, self.hhdc_account, self.msn, self.pc, self.mtc,
            self.cop, self.ssc, self.imp_mpan_core,
            None if self.imp_llfc is None else self.imp_llfc.code,
            self.imp_supplier_contract, self.imp_supplier_account, self.imp_sc,
            self.exp_mpan_core,
            None if self.exp_llfc is None else self.exp_llfc.code,
            self.exp_supplier_contract, self.exp_supplier_account, self.exp_sc)

    def update(
            self, sess, start_date, finish_date, mop_contract, mop_account,
            hhdc_contract, hhdc_account, msn, pc, mtc, cop, ssc, imp_mpan_core,
            imp_llfc_code, imp_supplier_contract, imp_supplier_account, imp_sc,
            exp_mpan_core, exp_llfc_code, exp_supplier_contract,
            exp_supplier_account, exp_sc, do_check=None):

        orig_start_date = self.start_date
        orig_finish_date = self.finish_date

        if hh_after(start_date, finish_date):
            raise BadRequest(
                "The era start date can't be after the finish date.")

        if imp_mpan_core is None and exp_mpan_core is None:
            raise BadRequest("An era must have at least one MPAN.")

        if mop_contract is None:
            raise BadRequest("An supply era must have a MOP contract.")

        mop_account = mop_account.strip()
        if len(mop_account) == 0:
            raise BadRequest("There must be a MOP account reference.")

        if hhdc_contract is None:
            raise BadRequest("An era must have an HHDC contract.")

        hhdc_account = hhdc_account.strip()
        if len(hhdc_account) == 0:
            raise BadRequest("There must be an account reference.")

        self.msn = msn
        self.pc = pc
        self.ssc = ssc
        locs = locals()
        voltage_level = None
        self.cop = cop
        self.mtc = mtc

        self.start_date = start_date
        self.finish_date = finish_date
        self.scc = ssc
        self.mop_account = mop_account
        self.mop_contract = mop_contract
        self.hhdc_account = hhdc_account
        self.hhdc_contract = hhdc_contract

        for polarity in ['imp', 'exp']:
            mcore_str = locs[polarity + '_mpan_core']
            if mcore_str is None:
                for suf in [
                        'mpan_core', 'llfc', 'supplier_contract',
                        'supplier_account', 'sc']:
                    setattr(self, polarity + '_' + suf, None)
                continue

            mcore = parse_mpan_core(mcore_str)

            if mcore[:2] != self.supply.dno_contract.name:
                raise BadRequest(
                    "The DNO code of the MPAN core " + mcore +
                    "doesn't match the DNO code of the supply.")

            setattr(self, polarity + '_mpan_core', mcore)

            supplier_contract = locs[polarity + '_supplier_contract']
            if supplier_contract is None:
                raise BadRequest(
                    "There's an " + polarity + " MPAN core, but no " +
                    polarity + " supplier contract.")
            if supplier_contract.start_date() > start_date:
                raise BadRequest(
                    "The supplier contract starts after the era.")

            if hh_before(supplier_contract.finish_date(), finish_date):
                raise BadRequest("""The supplier contract finishes
                        before the era.""")
            supplier_account = locs[polarity + '_supplier_account']
            setattr(self, polarity + '_supplier_contract', supplier_contract)
            setattr(self, polarity + '_supplier_account', supplier_account)

            llfc_code = locs[polarity + '_llfc_code']
            llfc = self.supply.dno_contract.party.get_llfc_by_code(
                sess, llfc_code)
            if llfc.is_import != ('imp' == polarity):
                raise BadRequest(
                    "The " + polarity + " line loss factor " + llfc.code +
                    " is actually an " +
                    ("imp" if llfc.is_import else "exp") + " one.")
            vl = llfc.voltage_level
            if voltage_level is None:
                voltage_level = vl
            elif voltage_level != vl:
                raise BadRequest(
                    "The voltage level indicated by the Line Loss Factor "
                    "must be the same for both the MPANs.")
            setattr(self, polarity + '_llfc', llfc)
            sc = locs[polarity + '_sc']
            if sc is None:
                raise BadRequest(
                    "There's an " + polarity + " MPAN core, but no " +
                    polarity + " Supply Capacity.")

            setattr(self, polarity + '_sc', sc)

        if self.mtc.meter_type.code == "C5" and cop.code not in [
                "1", "2", "3", "4", "5"] or self.mtc.meter_type.code in [
                "6A", "6B", "6C", "6D"] and \
                cop.code.upper() != self.mtc.meter_type.code:
            raise BadRequest(
                "The CoP of " + cop.code +
                " is not compatible with the meter type code of " +
                self.mtc.meter_type.code + ".")

        if hhdc_contract.start_date() > start_date:
            raise BadRequest("The HHDC contract starts after the era.")

        if hh_before(hhdc_contract.finish_date(), finish_date):
            raise BadRequest(
                "The HHDC contract " + hhdc_contract.id +
                " finishes before the era.")

        if mop_contract.start_date() > start_date:
            raise BadRequest(
                "The MOP contract starts after the supply era.")

        if hh_before(mop_contract.finish_date(), finish_date):
            raise BadRequest(
                "The MOP contract " + mop_contract.id +
                " finishes before the era.")

        if pc.code == '00' and ssc is not None:
            raise BadRequest(
                "A supply with Profile Class 00 can't have " +
                "a Standard Settlement Configuration.")
        if pc.code != '00' and ssc is None:
            raise BadRequest(
                "A NHH supply must have a Standard Settlement Configuration.")

        try:
            sess.flush()
        except ProgrammingError as e:
            if e.orig.args[2] == 'null value in column "start_date" ' + \
                    'violates not-null constraint':
                raise BadRequest("The start date cannot be blank.")
            else:
                raise e

        prev_era = self.supply.find_era_at(sess, prev_hh(orig_start_date))
        next_era = self.supply.find_era_at(sess, next_hh(orig_finish_date))

        if prev_era is not None:
            is_overlap = False
            if imp_mpan_core is not None:
                prev_imp_mpan_core = prev_era.imp_mpan_core
                if prev_imp_mpan_core is not None and imp_mpan_core == \
                        prev_imp_mpan_core:
                    is_overlap = True
            if not is_overlap and exp_mpan_core is not None:
                prev_exp_mpan_core = prev_era.exp_mpan_core
                if prev_exp_mpan_core is not None and exp_mpan_core == \
                        prev_exp_mpan_core:
                    is_overlap = True
            if not is_overlap:
                raise BadRequest(
                    "MPAN cores can't change without an overlapping period.")

        if next_era is not None:
            is_overlap = False
            if imp_mpan_core is not None:
                next_imp_mpan_core = next_era.imp_mpan_core
                if next_imp_mpan_core is not None and \
                        imp_mpan_core == next_imp_mpan_core:
                    is_overlap = True
            if not is_overlap and exp_mpan_core is not None:
                next_exp_mpan_core = next_era.exp_mpan_core
                if next_exp_mpan_core is not None and exp_mpan_core \
                        == next_exp_mpan_core:
                    is_overlap = True
            if not is_overlap:
                raise BadRequest(
                    "MPAN cores can't change without an overlapping period.")

        sess.flush()

    def insert_channel(self, sess, imp_related, channel_type):
        channel = Channel(self, imp_related, channel_type)
        try:
            sess.add(channel)
            sess.flush()
        except SQLAlchemyError as e:
            sess.rollback()
            raise BadRequest(
                "There's already a channel with import related: " +
                str(imp_related) + " and channel type: " +
                str(channel_type) + "." + str(e))

        channel.add_snag(sess, Snag.MISSING, self.start_date, self.finish_date)
        return channel

    def set_physical_location(self, sess, site):
        target_ssgen = sess.query(SiteEra).filter(
            SiteEra.era == self, SiteEra.site == site).first()
        if target_ssgen is None:
            raise BadRequest("The site isn't attached to this supply.")

        for ssgen in self.site_eras:
            ssgen.is_physical = ssgen == target_ssgen
        sess.flush()

    def delete_channel(self, sess, imp_related, channel_type):
        channel = self.get_channel(sess, imp_related, channel_type)
        if sess.query(HhDatum).filter(HhDatum.channel == channel).count() > 0:
            raise BadRequest(
                "One can't delete a channel if there are still HH data "
                "attached to it.")

        for snag in sess.query(Snag).filter(Snag.channel == channel):
            sess.delete(snag)

        sess.delete(channel)
        sess.flush()

    def make_meter_category(self):
        if self.pc.code == '00':
            return 'hh'
        elif len(self.channels) > 0:
            return 'amr'
        elif self.mtc.meter_type.code in ['UM', 'PH']:
            return 'unmetered'
        else:
            return 'nhh'


class Channel(Base, PersistentClass):
    __tablename__ = 'channel'
    id = Column(Integer, primary_key=True)
    era_id = Column(Integer, ForeignKey('era.id'))
    imp_related = Column(Boolean, nullable=False)
    channel_type = Column(
        Enum('ACTIVE', 'REACTIVE_IMP', 'REACTIVE_EXP', name='channel_type'),
        nullable=False)
    hh_data = relationship('HhDatum', backref='channel')
    snag = relationship('Snag', backref='channel')

    def __init__(self, era, imp_related, channel_type):
        self.era = era
        self.imp_related = imp_related
        self.channel_type = channel_type

    def site_check(self, sess, start_date, finish_date):
        if self.channel_type == 'ACTIVE':
            site = sess.query(Site).join(SiteEra).filter(
                SiteEra.era == self.era, SiteEra.is_physical == true()).one()

            if start_date > self.era.start_date:
                check_from = start_date
            else:
                check_from = self.era.start_date

            if hh_before(finish_date, self.era.finish_date):
                check_to = finish_date
            else:
                check_to = self.era.finish_date

            site.hh_check(sess, check_from, check_to)

    def add_snag(self, sess, description, start_date, finish_date):
        Snag.add_snag(sess, None, self, description, start_date, finish_date)

    def remove_snag(self, sess, description, start_date, finish_date):
        Snag.remove_snag(
            sess, None, self, description, start_date, finish_date)

    def delete_data(self, sess, start, finish):
        if start < self.era.start_date:
            raise BadRequest(
                "The start date is before the beginning of the era.")
        if hh_after(finish, self.era.finish_date):
            raise BadRequest("The finish date is after the end of the era.")

        num_rows = sess.query(HhDatum).filter(
            HhDatum.channel == self, HhDatum.start_date >= start,
            HhDatum.start_date <= finish).count()
        if num_rows == 0:
            raise BadRequest(
                "There aren't any data to delete for this period.")

        sess.execute(
            "delete from hh_datum where hh_datum.channel_id = :channel_id and "
            "hh_datum.start_date >= :start and hh_datum.start_date "
            "<= :finish",
            {'channel_id': self.id, 'start': start, 'finish': finish})

        self.add_snag(sess, Snag.MISSING, start, finish)
        self.site_check(sess, start, finish)

    def add_hh_data(self, sess, data_raw):
        set_read_write(sess)
        data = iter(sess.query(HhDatum).filter(
            HhDatum.channel == self,
            HhDatum.start_date >= data_raw[0]['start_date'],
            HhDatum.start_date <= data_raw[-1]['start_date']).order_by(
            HhDatum.start_date))

        try:
            datum = next(data)
            datum_date = datum.start_date
        except StopIteration:
            datum_date = None

        insert_blocks, insert_date = [], None
        update_blocks, update_date = [], None
        upsert_blocks, upsert_date = [], None
        estimate_blocks, estimate_date = [], None
        negative_blocks, negative_date = [], None

        for datum_raw in data_raw:
            datum_raw['channel_id'] = self.id
            if datum_raw['start_date'] == datum_date:
                if (datum.value, datum.status) != \
                        (datum_raw['value'], datum_raw['status']):
                    if update_date != datum_raw['start_date']:
                        update_block = []
                        update_blocks.append(update_block)
                    datum_raw['id'] = datum.id
                    update_block.append(datum_raw)
                    update_date = datum_raw['start_date'] + HH
                    if upsert_date != datum_raw['start_date']:
                        upsert_block = []
                        upsert_blocks.append(upsert_block)
                    upsert_block.append(datum_raw)
                    upsert_date = datum_raw['start_date'] + HH
                try:
                    datum = next(data)
                    sess.expunge(datum)
                    datum_date = datum.start_date
                except StopIteration:
                    datum_date = None
            else:
                if datum_raw['start_date'] != insert_date:
                    insert_block = []
                    insert_blocks.append(insert_block)
                insert_block.append(datum_raw)
                insert_date = datum_raw['start_date'] + HH
                if upsert_date != datum_raw['start_date']:
                    upsert_block = []
                    upsert_blocks.append(upsert_block)
                upsert_block.append(datum_raw)
                upsert_date = datum_raw['start_date'] + HH

            if upsert_date is not None and \
                    upsert_date > datum_raw['start_date']:
                if datum_raw['status'] == 'E':
                    if estimate_date != datum_raw['start_date']:
                        estimate_block = []
                        estimate_blocks.append(estimate_block)
                    estimate_block.append(datum_raw)
                    estimate_date = datum_raw['start_date'] + HH
                if datum_raw['value'] < 0:
                    if negative_date != datum_raw['start_date']:
                        negative_block = []
                        negative_blocks.append(negative_block)
                    negative_block.append(datum)
                    negative_date = datum_raw['start_date'] + HH

        for b in insert_blocks:
            sess.execute(
                "INSERT INTO hh_datum (channel_id, start_date, value, "
                "status, last_modified) VALUES "
                "(:channel_id, :start_date, :value, :status, "
                "current_timestamp)", params=b)
            sess.flush()
            self.remove_snag(
                sess, Snag.MISSING, b[0]['start_date'], b[-1]['start_date'])
            sess.flush()

        for block in update_blocks:
            start_date = block[0]['start_date']
            finish_date = block[-1]['start_date']
            for dw in block:
                sess.execute(
                    "update hh_datum set value = :value, status = :status, "
                    "last_modified = current_timestamp where id = :id",
                    params={
                        'value': dw['value'], 'status': dw['status'],
                        'id': dw['id']})
            self.remove_snag(sess, Snag.NEGATIVE, start_date, finish_date)
            self.remove_snag(sess, Snag.ESTIMATED, start_date, finish_date)
            sess.flush()

        for b in upsert_blocks:
            self.site_check(sess, b[0]['start_date'], b[-1]['start_date'])
            sess.flush()

        for b in negative_blocks:
            self.add_snag(
                sess, Snag.NEGATIVE, b[0]['start_date'], b[-1]['start_date'])
            sess.flush()

        for b in estimate_blocks:
            self.add_snag(
                sess, Snag.ESTIMATED, b[0]['start_date'], b[-1]['start_date'])
            sess.flush()

        sess.commit()
        sess.flush()


class Supply(Base, PersistentClass):
    @staticmethod
    def get_by_mpan_core(sess, mpan_core):
        supply = Supply.find_by_mpan_core(sess, mpan_core)
        if supply is None:
            raise BadRequest(
                "The MPAN core " + mpan_core + " is not set up in Chellow.")
        return supply

    @staticmethod
    def find_by_mpan_core(sess, mpan_core):
        if mpan_core is None:
            return None
        else:
            return sess.query(Supply).join(Era).distinct().filter(
                or_(
                    Era.imp_mpan_core == mpan_core,
                    Era.exp_mpan_core == mpan_core)).first()

    @staticmethod
    def _settle_stripe(sess, start_date, finish_date, old_era, new_era):

        # move snags from old to new
        if old_era is None:
            for channel in sess.query(Channel).filter(
                    Channel.era == new_era).order_by(Channel.id):
                channel.add_snag(sess, Snag.MISSING, start_date, finish_date)

        if new_era is None:
            for channel in sess.query(Channel).filter(
                    Channel.era == old_era).order_by(Channel.id):
                for desc in [Snag.MISSING, Snag.NEGATIVE, Snag.ESTIMATED]:
                    channel.remove_snag(sess, desc, start_date, finish_date)

                hh_data = sess.query(HhDatum).filter(
                    HhDatum.channel == channel,
                    HhDatum.start_date >= start_date)
                if finish_date is not None:
                    hh_data = hh_data.filter(HhDatum.start_date <= finish_date)
                if hh_data.count() > 0:
                    raise BadRequest(
                        "There are orphaned HH data between " +
                        hh_format(start_date) + " and " +
                        hh_format(finish_date) + ".")

        if old_era is not None and new_era is not None:
            for channel in sess.query(Channel).filter(
                    Channel.era == old_era).order_by(Channel.id):

                snags = sess.query(Snag).filter(
                    Snag.channel == channel, or_(
                        Snag.finish_date == null(),
                        Snag.finish_date >= start_date)).order_by(Snag.id)
                if finish_date is not None:
                    snags = snags.filter(Snag.start_date <= finish_date)
                target_channel = new_era.find_channel(
                    sess, channel.imp_related, channel.channel_type)

                for snag in snags:
                    snag_start = max(snag.start_date, start_date)
                    snag_finish = snag.finish_date if \
                        hh_before(snag.finish_date, finish_date) else \
                        finish_date
                    if target_channel is not None:
                        target_channel.add_snag(
                            sess, snag.description, snag_start, snag_finish)
                    channel.remove_snag(
                        sess, snag.description, snag_start, snag_finish)

                hh_data = sess.query(HhDatum).filter(
                    HhDatum.channel == channel,
                    HhDatum.start_date >= start_date)
                if finish_date is not None:
                    hh_data = hh_data.filter(HhDatum.start_date <= finish_date)

                if hh_data.count() > 0:
                    if target_channel is None:
                        raise Exception(
                            "There is no channel for the import related: " +
                            str(channel.imp_related) + " and channel type: " +
                            str(channel.channel_type) + " HH data from " +
                            str(start_date) +
                            " to move to in the era starting " +
                            str(new_era.start_date) + ", finishing " +
                            str(new_era.finish_date) + ".")

                    c_params = {
                        'channel_id': channel.id,
                        'target_channel_id': target_channel.id,
                        'start_date': start_date}
                    if finish_date is not None:
                        c_params['finish_date'] = finish_date

                    sess.execute(
                        "update hh_datum set channel_id = :target_channel_id "
                        "where start_date >= :start_date and "
                        "channel_id = :channel_id" +
                        ("" if finish_date is None
                            else " and start_date <= :finish_date"), c_params)

    __tablename__ = 'supply'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    note = Column(Text, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)
    generator_type_id = Column(Integer, ForeignKey('generator_type.id'))
    gsp_group_id = Column(
        Integer, ForeignKey('gsp_group.id'), nullable=False)
    dno_contract_id = Column(
        Integer, ForeignKey('contract.id'), nullable=False)
    eras = relationship('Era', backref='supply', order_by='Era.start_date')
    bills = relationship('Bill', backref='supply')

    def __init__(self, name, source, generator_type, gsp_group, dno_contract):
        self.note = ''
        self.update(name, source, generator_type, gsp_group, dno_contract)

    def update(self, name, source, generator_type, gsp_group, dno_contract):
        if name is None:
            raise Exception("The supply name cannot be null.")

        name = name.strip()
        if len(name) == 0:
            raise BadRequest("The supply name can't be blank.")

        self.name = name
        self.source = source
        if source.code in ('gen', 'gen-net') and generator_type is None:
            raise BadRequest(
                "If the source is 'gen' or 'gen-net', there " +
                "must be a generator type.")

        if source.code == 'net' and dno_contract.name == "99":
            raise BadRequest(
                "A network supply can't have a DNO code  of 99.")

        if source.code in ('gen', 'gen-net'):
            self.generator_type = generator_type
        else:
            self.generator_type = None

        self.gsp_group = gsp_group
        self.dno_contract = dno_contract

    def find_era_at(self, sess, dt):
        if dt is None:
            return sess.query(Era).filter(
                Era.supply == self, Era.finish_date == null()).first()
        else:
            return sess.query(Era).filter(
                Era.supply == self, Era.start_date <= dt, or_(
                    Era.finish_date == null(), Era.finish_date >= dt)).first()

    def find_last_era(self, sess):
        return sess.query(Era).filter(
            Era.supply == self).order_by(Era.start_date.desc()).first()

    def find_eras(self, sess, start, finish):
        eras = sess.query(Era).filter(
            Era.supply == self, or_(
                Era.finish_date == null(), Era.finish_date >= start)).order_by(
            Era.start_date)
        if finish is not None:
            eras = eras.filter(Era.start_date <= finish)
        return eras.all()

    def update_era(
            self, sess, era, start_date, finish_date, mop_contract,
            mop_account, hhdc_contract, hhdc_account, msn, pc, mtc_code, cop,
            ssc, imp_mpan_core, imp_llfc_code, imp_supplier_contract,
            imp_supplier_account, imp_sc, exp_mpan_core, exp_llfc_code,
            exp_supplier_contract, exp_supplier_account, exp_sc):
        if era.supply != self:
            raise Exception("The era doesn't belong to this supply.")

        for mc in (imp_mpan_core, exp_mpan_core):
            if mc is not None:
                sup = sess.query(Era).filter(
                    Era.supply != self,
                    or_(
                        Era.imp_mpan_core == mc,
                        Era.exp_mpan_core == mc)).first()
                if sup is not None:
                    raise BadRequest(
                        "The MPAN core " + mc +
                        " is already attached to another supply.")

        old_stripes = []
        new_stripes = []
        prev_era = self.find_era_at(sess, prev_hh(era.start_date))
        if prev_era is None:
            old_stripes.append(
                {
                    'start_date': datetime.datetime(
                        datetime.MINYEAR, 1, 2, tzinfo=pytz.utc),
                    'finish_date': era.start_date - HH, 'era': None})
            new_stripes.append(
                {
                    'start_date': datetime.datetime(
                        datetime.MINYEAR, 1, 2, tzinfo=pytz.utc),
                    'finish_date': start_date - HH, 'era': None})
        else:
            old_stripes.append(
                {
                    'start_date': prev_era.start_date,
                    'finish_date': prev_era.finish_date, 'era': prev_era})
            new_stripes.append(
                {
                    'start_date': prev_era.start_date,
                    'finish_date': start_date - HH, 'era': prev_era})

        if era.finish_date is None:
            next_era = None
        else:
            next_era = self.find_era_at(sess, next_hh(era.finish_date))

        if next_era is None:
            if era.finish_date is not None:
                old_stripes.append(
                    {
                        'start_date': era.finish_date + HH,
                        'finish_date': None, 'era': None})
            if finish_date is not None:
                new_stripes.append(
                    {
                        'start_date': finish_date + HH,
                        'finish_date': None, 'era': None})
        else:
            old_stripes.append(
                {
                    'start_date': next_era.start_date,
                    'finish_date': next_era.finish_date, 'era': next_era})
            if finish_date is not None:
                new_stripes.append(
                    {
                        'start_date': finish_date + HH,
                        'finish_date': next_era.finish_date, 'era': next_era})

        old_stripes.append(
            {
                'start_date': era.start_date, 'finish_date': era.finish_date,
                'era': era})
        new_stripes.append(
            {
                'start_date': start_date, 'finish_date': finish_date,
                'era': era})

        for old_stripe in old_stripes:
            for new_stripe in new_stripes:
                if not hh_after(
                        old_stripe['start_date'],
                        new_stripe['finish_date']) and not hh_before(
                        old_stripe['finish_date'],
                        new_stripe['start_date']) and \
                        old_stripe['era'] != new_stripe['era']:
                    stripe_start = max(
                        old_stripe['start_date'], new_stripe['start_date'])
                    stripe_finish = old_stripe['finish_date'] if \
                        hh_before(
                            old_stripe['finish_date'],
                            new_stripe['finish_date']) else \
                        new_stripe['finish_date']
                    Supply._settle_stripe(
                        sess, stripe_start, stripe_finish, old_stripe['era'],
                        new_stripe['era'])

        era.update(
            sess, start_date, finish_date, mop_contract, mop_account,
            hhdc_contract, hhdc_account, msn, pc, mtc_code, cop, ssc,
            imp_mpan_core, imp_llfc_code, imp_supplier_contract,
            imp_supplier_account, imp_sc, exp_mpan_core, exp_llfc_code,
            exp_supplier_contract, exp_supplier_account, exp_sc)

        if prev_era is not None:
            prev_era.update_dates(
                sess, prev_era.start_date, prev_hh(start_date))

        if next_era is not None:
            next_era.update_dates(
                sess, next_hh(finish_date), next_era.finish_date)

    def insert_era_at(self, sess, start_date):
        if len(self.eras) == 0:
            raise BadRequest(
                "Can't insert era as there aren't any existing eras")

        if hh_after(start_date, self.find_last_era(sess).finish_date):
            raise BadRequest(
                "One can't add an era that starts after the "
                "supply has finished.")

        first_era = self.find_first_era(sess)

        if start_date < first_era.start_date:
            template_era = first_era
        else:
            template_era = self.find_era_at(sess, start_date)

        logical_sites = []
        physical_site = None
        for site_era in template_era.site_eras:
            if site_era.is_physical:
                physical_site = site_era.site
            else:
                logical_sites.append(site_era.site)

        channel_set = set(
            [(imp_related, channel_type) for imp_related in [True, False]
                for channel_type in CHANNEL_TYPES if template_era.find_channel(
                    sess, imp_related, channel_type) is not None])

        if template_era.imp_mpan_core is None:
            imp_llfc_code = None
        else:
            imp_llfc_code = template_era.imp_llfc.code

        if template_era.exp_mpan_core is None:
            exp_llfc_code = None
        else:
            exp_llfc_code = template_era.exp_llfc.code

        return self.insert_era(
            sess, physical_site, logical_sites, start_date, None,
            template_era.mop_contract, template_era.mop_account,
            template_era.hhdc_contract, template_era.hhdc_account,
            template_era.msn, template_era.pc, template_era.mtc,
            template_era.cop, template_era.ssc, template_era.imp_mpan_core,
            imp_llfc_code, template_era.imp_supplier_contract,
            template_era.imp_supplier_account, template_era.imp_sc,
            template_era.exp_mpan_core, exp_llfc_code,
            template_era.exp_supplier_contract,
            template_era.exp_supplier_account, template_era.exp_sc,
            channel_set)

    def insert_era(
            self, sess, physical_site, logical_sites, start_date, finish_date,
            mop_contract, mop_account, hhdc_contract, hhdc_account, msn, pc,
            mtc, cop, ssc, imp_mpan_core, imp_llfc_code, imp_supplier_contract,
            imp_supplier_account, imp_sc, exp_mpan_core, exp_llfc_code,
            exp_supplier_contract, exp_supplier_account, exp_sc, channel_set):
        covered_era = None

        if len(self.eras) > 0:
            if hh_after(start_date, self.find_last_era(sess).finish_date):
                raise BadRequest(
                    "One can't add a era that starts after "
                    "the supply has finished.")

            first_era = self.find_first_era(sess)

            if hh_before(start_date, first_era.start_date):
                finish_date = prev_hh(first_era.start_date)
            else:
                covered_era = self.find_era_at(sess, start_date)
                if start_date == covered_era.start_date:
                    raise BadRequest(
                        "There's already an era with that start date.")

                finish_date = covered_era.finish_date

        for mc in (imp_mpan_core, exp_mpan_core):
            if mc is not None:
                sup = sess.query(Era).filter(
                    Era.supply != self,
                    or_(
                        Era.imp_mpan_core == mc,
                        Era.exp_mpan_core == mc)).first()
                if sup is not None:
                    raise BadRequest(
                        "The MPAN core " + mc +
                        " is already attached to another supply.")

        sess.flush()
        era = Era(
            sess, self, start_date, finish_date, mop_contract, mop_account,
            hhdc_contract, hhdc_account, msn, pc, mtc, cop, ssc, imp_mpan_core,
            imp_llfc_code, imp_supplier_contract, imp_supplier_account, imp_sc,
            exp_mpan_core, exp_llfc_code, exp_supplier_contract,
            exp_supplier_account, exp_sc)
        sess.add(era)
        sess.flush()

        for imp_related, channel_type in sorted(list(channel_set)):
            sess.add(Channel(era, imp_related, channel_type))

        sess.flush()
        era.attach_site(sess, physical_site, True)
        for site in logical_sites:
            era.attach_site(sess, site, False)

        sess.flush()
        Supply._settle_stripe(sess, start_date, finish_date, covered_era, era)

        sess.flush()
        if covered_era is not None:
            covered_era.update_dates(
                sess, covered_era.start_date, start_date - HH)

        return era

    def find_first_era(self, sess):
        return sess.query(Era).filter(Era.supply == self).order_by(
            Era.start_date).first()

    def delete_era(self, sess, era):
        if len(self.eras) == 1:
            raise BadRequest(
                "The only way to delete the last era is to "
                "delete the entire supply.")

        prev_era = self.find_era_at(sess, prev_hh(era.start_date))
        if era.finish_date is None:
            next_era = None
        else:
            next_era = self.find_era_at(sess, next_hh(era.finish_date))

        Supply._settle_stripe(
            sess, era.start_date, era.finish_date, era,
            next_era if prev_era is None else prev_era)

        if prev_era is None:
            next_era.update_dates(sess, era.start_date, next_era.finish_date)
        else:
            prev_era.update_dates(sess, prev_era.start_date, era.finish_date)

        for site_era in era.site_eras:
            sess.delete(site_era)
        sess.flush()
        for channel in era.channels:
            era.delete_channel(sess, channel.imp_related, channel.channel_type)
        sess.delete(era)
        sess.flush()

    def delete(self, sess):
        if len(self.bills) > 0:
            BadRequest(
                "One can't delete a supply if there are still "
                "bills attached to it.")

        for era in self.eras:
            for site_era in era.site_eras:
                sess.delete(site_era)
            sess.flush()
            for channel in era.channels:
                era.delete_channel(
                    sess, channel.imp_related, channel.channel_type)
                sess.flush()
            sess.delete(era)
            sess.flush()

        sess.flush()

        sess.delete(self)
        sess.flush()

    def site_check(self, sess, start, finish):
        for era in self.eras:
            for imp_related in (True, False):
                era.find_channel(sess, imp_related, 'ACTIVE').site_check(
                    sess, start, finish)


class HhDatum(Base, PersistentClass):
    # status A actual, E estimated, C padding
    @staticmethod
    def insert(sess, raw_data):
        mpan_core = channel_type = prev_date = era_finish_date = None
        data = []
        channel = None
        for datum in raw_data:
            if len(data) > 1000 or not (
                    mpan_core == datum['mpan_core'] and
                    datum['channel_type'] == channel_type and
                    datum['start_date'] == prev_date + HH) or (
                    era_finish_date is not None and
                    era_finish_date < datum['start_date']):
                if len(data) > 0:
                    channel.add_hh_data(sess, data)
                    data = []
                mpan_core = datum['mpan_core']
                supply = Supply.get_by_mpan_core(sess, mpan_core)
                era = supply.find_era_at(sess, datum['start_date'])
                if era is None:
                    raise BadRequest(
                        "This datum is either before or after the supply: " +
                        str(datum) + ".")

                channel_type = datum['channel_type']
                channel = era.find_channel(
                    sess, mpan_core == era.imp_mpan_core, channel_type)
                if channel is None:
                    vals = []
                    for k in sorted(datum.keys()):
                        vals.append("'" + k + "': " + repr(datum[k]))
                    raise BadRequest(
                        "There is no channel for the datum: {" +
                        ', '.join(vals) + "}.")

                era_finish_date = era.finish_date
            prev_date = datum['start_date']
            data.append(datum)
        if len(data) > 0:
            channel.add_hh_data(sess, data)

    __tablename__ = 'hh_datum'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channel.id'))
    start_date = Column(DateTime(timezone=True), nullable=False)
    value = Column(Numeric, nullable=False)
    status = Column(String, nullable=False)
    last_modified = Column(DateTime(timezone=True), nullable=False)
    __table_args__ = (UniqueConstraint('channel_id', 'start_date'),)

    def __init__(self, channel, datum_raw):
        self.channel = channel
        self.start_date = datum_raw['start_date']
        self.update(datum_raw['value'], datum_raw['status'])

    def __str__(self):
        buf = []
        for prop in (
                'status', 'start_date', 'channel_type', 'value', 'mpan_core'):
            buf.append("'" + prop + "': '" + str(getattr(self, prop)) + "'")
        return '{' + ', '.join(buf) + '}'

    def update(self, value, status):
        if status not in ('E', 'A', 'C'):
            raise BadRequest("The status character must be E, A or C.")

        self.value = value
        self.status = status
        nw = datetime.datetime.now(pytz.utc)
        self.last_modified = datetime.datetime(
            year=nw.year, month=nw.month, day=nw.day, tzinfo=pytz.utc)


class Report(Base, PersistentClass):

    __tablename__ = 'report'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    script = Column(Text, nullable=False)
    template = Column(Text)

    def __init__(self, name, script, template):
        self.name = name
        self.script = script
        self.template = template

    def update(self, name, script, template):
        self.name = name
        self.script = script
        if template is not None and len(template.strip()) == 0:
            template = None

        self.template = template


class SiteGroup():
    EXPORT_NET_GT_IMPORT_GEN = "Export to net > import from generators."
    EXPORT_GEN_GT_IMPORT = "Export to generators > import."

    def __init__(self, start_date, finish_date, sites, supplies):
        self.start_date = start_date
        self.finish_date = finish_date
        self.sites = sites
        self.supplies = supplies

    def hh_data(self, sess):
        keys = {
            'net': {True: ['imp_net'], False: ['exp_net']},
            'gen-net': {
                True: ['imp_net', 'exp_gen'], False: ['exp_net', 'imp_gen']},
            'gen': {True: ['imp_gen'], False: ['exp_gen']},
            '3rd-party': {True: ['imp_3p'], False: ['exp_3p']},
            '3rd-party-reverse': {True: ['exp_3p'], False: ['imp_3p']}}
        data = []

        if len(self.supplies) == 0:
            channels = []
        else:
            channels = sess.query(Channel).join(Era, Supply, Source).filter(
                Era.supply_id.in_([sup.id for sup in self.supplies]),
                Era.start_date <= self.finish_date, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= self.start_date),
                Source.code != 'sub', Channel.channel_type == 'ACTIVE').all()

        channel_keys = dict(
            (
                c.id, keys[c.era.supply.source.code][c.imp_related])
            for c in channels)
        hh_start = self.start_date

        if len(channels) == 0:
            hh = None
        else:
            db_data = iter(
                sess.execute(
                    "select start_date, value, channel_id from hh_datum "
                    "where channel_id = any(:channel_ids) "
                    "and start_date >= :start_date "
                    "and start_date <= :finish_date order by start_date",
                    {
                        'channel_ids': [c.id for c in channels],
                        'start_date': self.start_date,
                        'finish_date': self.finish_date}))

            hh = next(db_data, None)

        while hh_start <= self.finish_date:
            dd = {
                'start_date': hh_start, 'imp_net': 0, 'exp_net': 0,
                'imp_gen': 0, 'exp_gen': 0, 'imp_3p': 0, 'exp_3p': 0}
            data.append(dd)
            while hh is not None and hh.start_date == hh_start:
                for key in channel_keys[hh.channel_id]:
                    dd[key] += hh.value
                hh = next(db_data, None)

            dd['displaced'] = dd['imp_gen'] - dd['exp_gen'] - dd['exp_net']
            dd['used'] = dd['displaced'] + dd['imp_net'] + dd['imp_3p'] - \
                dd['exp_3p']
            hh_start += HH

        return data

    def add_snag(self, sess, description, start_date, finish_date):
        return Snag.add_snag(
            sess, self.sites[0], None, description, start_date, finish_date)

    def delete_snag(self, sess, description, start_date, finish_date):
        Snag.remove_snag(
            sess, self.sites[0], None, description, start_date, finish_date)


def read_file(pth, fname, attr):
    with open(os.path.join(pth, fname), 'r') as f:
        contents = f.read()
    if attr is None:
        return eval(contents)
    else:
        return {attr: contents}


def db_init(sess, root_path):
    db_name = config['PGDATABASE']
    log_message("Initializing database.")
    Base.metadata.create_all(bind=engine)
    for code, desc in (
            ("LV", "Low voltage"),
            ("HV", "High voltage"),
            ("EHV", "Extra high voltage")):
        sess.add(VoltageLevel(code, desc))
    sess.commit()

    set_read_write(sess)
    for code in ("editor", "viewer", "party-viewer"):
        sess.add(UserRole(code))
    sess.commit()

    set_read_write(sess)
    for code, desc in (
            ('net', "Public distribution system."),
            ('sub', "Sub meter"),
            ('gen-net', "Generator connected directly to network."),
            ('gen', "Generator."),
            ('3rd-party', "Third party supply."),
            (
                '3rd-party-reverse',
                "Third party supply with import going out of the site."),
            ):
        sess.add(Source(code, desc))
    sess.commit()

    set_read_write(sess)
    for code, desc in (
            ("chp", "Combined heat and power."),
            ("lm", "Load management."),
            ("turb", "Water turbine."),
            ("pv", "Solar Photovoltaics.")):
        sess.add(GeneratorType(code, desc))
    sess.commit()

    set_read_write(sess)
    for code, desc in (
            ("N", "Normal"),
            ("N3", "Normal 3rd Party"),
            ("C", "Customer"),
            ("E", "Estimated"),
            ("E3", "Estimated 3rd Party"),
            ("EM", "Estimated Manual"),
            ("W", "Withdrawn"),
            ("X", "Exchange"),
            ("CP", "Computer"),
            ("IF", "Information")):
        sess.add(ReadType(code, desc))
    sess.commit()

    set_read_write(sess)
    for code, desc in (
            ('1', "CoP 1"),
            ('2', "CoP 2"),
            ('3', "CoP 3"),
            ('4', "CoP 4"),
            ('5', "CoP 5"),
            ('6a', "CoP 6a 20 day memory"),
            ('6b', "CoP 6b 100 day memory"),
            ('6c', "CoP 6c 250 day memory"),
            ('6d', "CoP 6d 450 day memory"),
            ('7', "CoP 7")):
        sess.add(Cop(code, desc))
    sess.commit()

    set_read_write(sess)
    for code, desc in (
            ("F", "Final"),
            ("N", "Normal"),
            ("W", "Withdrawn")):
        sess.add(BillType(code, desc))
    sess.commit()

    dbapi_conn = sess.connection().connection.connection
    cursor = dbapi_conn.cursor()
    mdd_path = os.path.join(root_path, 'mdd')
    for tname, fname in (
            ("gsp_group", "GSP_Group"),
            ("pc", "Profile_Class"),
            ("market_role", "Market_Role"),
            ("participant", "Market_Participant"),
            ("party", "Market_Participant_Role"),
            ("llfc", "Line_Loss_Factor_Class"),
            ("meter_type", "MTC_Meter_Type"),
            ("meter_payment_type", "MTC_Payment_Type"),
            ("mtc", "Meter_Timeswitch_Class"),
            ("tpr", "Time_Pattern_Regime"),
            ("clock_interval", "Clock_Interval"),
            ("ssc", "Standard_Settlement_Configuration"),
            ("measurement_requirement", "Measurement_Requirement")):
        f = open(os.path.join(mdd_path, fname + '.csv'), 'rb')
        cursor.execute(
            "set transaction isolation level serializable read write")
        if tname == 'llfc':
            cursor.execute(
                "COPY " + tname +
                " (dno_id, code, description, voltage_level_id, "
                "is_substation, is_import, valid_from, valid_to) "
                "FROM STDIN CSV HEADER", stream=f)
        elif tname == 'participant':
            cursor.execute(
                "COPY " + tname + " (code, name) "
                "FROM STDIN CSV HEADER", stream=f)
        elif tname == 'market_role':
            cursor.execute(
                "COPY " + tname + " (code, description) "
                "FROM STDIN CSV HEADER", stream=f)
        elif tname == 'party':
            cursor.execute(
                "COPY " + tname + " (market_role_id, participant_id, "
                "name, valid_from, valid_to, dno_code) "
                "FROM STDIN CSV HEADER", stream=f)
        elif tname == 'meter_type':
            cursor.execute(
                "COPY " + tname + " (code, description, valid_from, "
                "valid_to) FROM STDIN CSV HEADER", stream=f)
        elif tname == 'mtc':
            cursor.execute(
                "COPY " + tname + " (dno_id, code, description, "
                "has_related_metering, has_comms, is_hh, meter_type_id, "
                "meter_payment_type_id, tpr_count, valid_from, valid_to) "
                "FROM STDIN CSV HEADER", stream=f)
        else:
            cursor.execute(
                "COPY " + tname + " FROM STDIN CSV HEADER", stream=f)
        dbapi_conn.commit()
        f.close()

    set_read_write(sess)
    for path_name, role_code in (
            ('non_core_contracts', 'Z'),
            ('dno_contracts', 'R')):
        contracts_path = os.path.join(root_path, path_name)

        for contract_name in sorted(os.listdir(contracts_path)):
            contract_path = os.path.join(contracts_path, contract_name)
            params = {'name': contract_name, 'charge_script': ''}
            for fname, attr in (
                    ('meta.py', None),
                    ('properties.py', 'properties'),
                    ('state.py', 'state')):
                params.update(read_file(contract_path, fname, attr))
            params['party'] = sess.query(Party).join(Participant). \
                join(MarketRole). \
                filter(
                    Participant.code == params['participant_code'],
                    MarketRole.code == role_code).one()
            del params['participant_code']
            contract = Contract(**params)
            sess.add(contract)

            sess.flush()
            rscripts_path = os.path.join(contract_path, 'rate_scripts')
            for rscript_fname in sorted(os.listdir(rscripts_path)):
                if not rscript_fname.endswith('.py'):
                    continue
                try:
                    start_str, finish_str = \
                        rscript_fname.split('.')[0].split('_')
                except ValueError:
                    raise Exception(
                        "The rate script " + rscript_fname +
                        " in the directory " + rscripts_path +
                        " should consist of two dates separated by an " +
                        "underscore.")
                start_date = datetime.datetime.strptime(
                    start_str, "%Y%m%d%H%M").replace(tzinfo=pytz.utc)
                if finish_str == 'ongoing':
                    finish_date = None
                else:
                    finish_date = datetime.datetime.strptime(
                        finish_str, "%Y%m%d%H%M").replace(tzinfo=pytz.utc)
                rparams = {
                    'start_date': start_date,
                    'finish_date': finish_date,
                    'contract': contract}
                rparams.update(
                    read_file(rscripts_path, rscript_fname, 'script'))
                sess.add(RateScript(**rparams))
                sess.flush()

            sess.flush()
            # Assign start and finish rate scripts
            scripts = sess.query(RateScript). \
                filter(RateScript.contract_id == contract.id). \
                order_by(RateScript.start_date).all()
            contract.start_rate_script = scripts[0]
            contract.finish_rate_script = scripts[-1]
    sess.commit()

    set_read_write(sess)
    sess.execute(
        "alter database " + db_name +
        " set default_transaction_isolation = 'serializable'")
    sess.execute(
        "alter database " + db_name +
        " set default_transaction_deferrable = on")
    sess.execute(
        "alter database " + db_name + " SET DateStyle TO 'ISO, YMD'")
    sess.execute(
        "alter database " + db_name +
        " set default_transaction_read_only = on")
    sess.commit()
    sess.close()
    engine.dispose()
    # Check the transaction isolation level is serializable
    isolation_level = sess.execute(
        "show transaction isolation level").scalar()
    if isolation_level != 'serializable':
        raise Exception(
            "The transaction isolation level for database " + db_name +
            " should be 'serializable' but in fact " "it's " +
            isolation_level + ".")

    set_read_write(sess)
    sess.execute("create extension tablefunc")
    conf = sess.query(Contract).join(MarketRole).filter(
        Contract.name == 'configuration', MarketRole.code == 'Z').one()
    state = conf.make_state()
    state['db_version'] = len(upgrade_funcs)
    conf.update_state(state)
    sess.commit()


def db_upgrade_0_to_1(sess):
    max_id = sess.execute("select max(id) from report;").scalar()
    sess.execute("create sequence report_id_seq start " + str(max_id + 1))
    sess.execute(
        "alter table report alter column id "
        "set default nextval('report_id_seq');")
    sess.execute("alter sequence report_id_seq owned by report.id;")


upgrade_funcs = [db_upgrade_0_to_1]


def db_upgrade(root_path):
    sess = None
    try:
        sess = Session()
        set_read_write(sess)
        db_version = find_db_version(sess)
        curr_version = len(upgrade_funcs)
        if db_version is None:
            log_message(
                "It looks like the chellow database hasn't been initialized.")
            db_init(sess, root_path)
        elif db_version == curr_version:
            log_message(
                "The database version is " + str(db_version) +
                " and the latest version is " + str(curr_version) +
                " so it doesn't look like you need to run an upgrade.")
        elif db_version > curr_version:
            log_message(
                "The database version is " + str(db_version) +
                " and the latest database version is " + str(curr_version) +
                " so it looks like you're using an old version of Chellow.")
        else:
            log_message(
                "Upgrading from database version " + str(db_version) +
                " to database version " + str(db_version + 1) + ".")
            upgrade_funcs[db_version](sess)
            conf = sess.query(Contract).join(MarketRole).filter(
                Contract.name == 'configuration', MarketRole.code == 'Z').one()
            state = conf.make_state()
            state['db_version'] = db_version + 1
            conf.update_state(state)
            sess.commit()
            log_message(
                "Successfully upgraded from database version " +
                str(db_version) + " to database version " +
                str(db_version + 1) + ".")
    finally:
        if sess is not None:
            sess.close()


def find_db_version(sess):
    engine = sess.get_bind()
    if engine.execute(
            """select count(*) from information_schema.tables """
            """where table_schema = 'public'""").scalar() == 0:
        return None
    conf = sess.query(Contract).join(MarketRole).filter(
        Contract.name == 'configuration', MarketRole.code == 'Z').one()
    conf_state = conf.make_state()
    return conf_state.get('db_version', 0)
