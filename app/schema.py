import logging

from sqlalchemy import MetaData, Table, Column, UniqueConstraint, Sequence, text
from sqlalchemy.dialects.postgresql import VARCHAR, BIGINT, INTEGER, TEXT, HSTORE, NUMERIC, TIMESTAMP, BOOLEAN, JSON

def get_tables(eng): 
    metadata_obj = MetaData(eng)
    TABLES = {}

    # TABLES[] = Table('tblname', metadata_obj, Column('id', SERIAL, primary_key=True)) 

    TABLES['audit_log'] = Table('audit_log', metadata_obj,
        Column('id', INTEGER, primary_key=True),
        Column('height', INTEGER, nullable=False),
        Column('created_at', DateTime(timezone=True), nullable=False, server_default=text('now()')),
        Column('service', VARCHAR(64), nullable=True),
        Column('notes', TEXT, nullable=True, default=0),
    )

    TABLES['announcements'] = Table('announcements', metadata_obj,
        Column('id', INTEGER, Sequence('announcements_id_seq', metadata=metadata_obj), primary_key=True),
        Column('createdTimestamp', DateTime(timezone=True), nullable=True, server_default=text('now()')),
        Column('title', TEXT, nullable=False),
        Column('shortDescription', TEXT, nullable=False),
        Column('description', TEXT, nullable=True),
        Column('bannerImgUrl', TEXT, nullable=False),
        Column('tag', TEXT, nullable=True),
    )

    TABLES['contributionEvents'] = Table('contributionEvents', metadata_obj,
        Column('id', INTEGER, Sequence('contributionEvents_id_seq', metadata=metadata_obj), primary_key=True),
        Column('projectName', TEXT, nullable=False),
        Column('roundName', TEXT, nullable=False),
        Column('eventId', INTEGER, nullable=False),
        Column('title', TEXT, nullable=False),
        Column('subtitle', TEXT, nullable=True),
        Column('details', TEXT, nullable=True),
        Column('checkBoxes', JSON, nullable=True, server_default='{}'),
        Column('tokenId', TEXT, nullable=False),
        Column('tokenName', TEXT, nullable=False),
        Column('tokenDecimals', INTEGER, nullable=False),
        Column('tokenPrice', NUMERIC(16, 6), nullable=False),
        Column('proxyNFTId', TEXT, nullable=False),
        Column('whitelistTokenId', TEXT, nullable=False),
        Column('additionalDetails', JSON, nullable=True, server_default='{}'),
    )

    TABLES['events'] = Table('events', metadata_obj,
        Column('id', INTEGER, Sequence('contributionEvents_id_seq', metadata=metadata_obj), primary_key=True),
        Column('name', TEXT, nullable=False),
        Column('description', TEXT, nullable=False),
        Column('blockChain', TEXT, nullable=True, server_default='ERGO'),
        Column('total_sigusd', NUMERIC(16, 6), nullable=True, server_default='0.0'),
        Column('buffer_sigusd', NUMERIC(16, 6), nullable=True, server_default='0.0'),
        Column('owner', TEXT, nullable=False, default='sigma@ergopad.io'),
        Column('walletId', INTEGER, nullable=True),
        Column('individualCap', INTEGER, nullable=True),
        Column('vestedTokenId', TEXT, nullable=True),
        Column('vestingPeriods', INTEGER, nullable=True),
        Column('vestingPeriodDuration', INTEGER, nullable=True),
        Column('vestingPeriodType', TEXT, nullable=True),
        Column('tokenPrice', INTEGER, nullable=True),
        Column('isWhitelist', INTEGER, nullable=True, server_default='0'),
        Column('start_dtz', DateTime(timezone=True), nullable=False, server_default=text('now()')),
        Column('end_dtz', DateTime(timezone=True), nullable=False, server_default=text('now()')),
        Column('whitelistTokenMultiplier', INTEGER, nullable=True, default=1),
    )

    return metadata_obj, TABLES

async def init_db(eng):
    # build tables, if needed
    try:
        # metadata_obj = MetaData(eng)
        metadata_obj, TABLES = get_tables(eng)
        metadata_obj.create_all(eng)

    except Exception as e:
        logging.error(f'ERR: {e}')
    
