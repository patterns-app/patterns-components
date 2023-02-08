#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./import_crunchbase.sh [Crunchbase API Key] [PG Database URL]"
    exit 1
fi

CRUNCHBASE_API_KEY=$1
PSQL_SCRIPTNAME=import_crunchbase.sql
TABLES="organizations category_groups people investors investments funds funding_rounds"
DB_URL=$2
TABLE_PREFIX="updated_crunchbase"

mkdir crunchbase_csv_split
cd crunchbase_csv_split
rm bulk_export_split.tar.gz
wget "https://api.crunchbase.com/bulk/v4/bulk_export_split.tar.gz?user_key=${CRUNCHBASE_API_KEY}" -O bulk_export_split.tar.gz
echo "Unzipping tar..."
tar xzf bulk_export_split.tar.gz

# clear file
> "$PSQL_SCRIPTNAME"

# drop data & schemas
for table in $TABLES; do
    echo "drop table if exists ${TABLE_PREFIX}_${table};" >> "$PSQL_SCRIPTNAME"
done

# write schemas first
cat <<EOT >> "$PSQL_SCRIPTNAME"
create table ${TABLE_PREFIX}_organizations (
    uuid        text primary key,
    name	    text,       
    type	    text,       
    permalink	text,       
    cb_url	    text,       
    rank	    double precision,       
    created_at	timestamp,  
    updated_at	timestamp,  
    legal_name	text,       
    roles	    text,       
    domain	    text,       
    homepage_url text,       
    country_code text,       
    state_code	text,       
    region	    text,       
    city	    text,       
    address	    text,       
    postal_code	text,       
    status	    text,
    short_description text,
    category_list text,
    category_groups_list	text,
    num_funding_rounds	double precision,   
    total_funding_usd	double precision,   
    total_funding	double precision,   
    total_funding_currency_code	text,
    founded_on	date,
    last_funding_on	date,
    closed_on	date,
    employee_count	text,
    email	text,
    phone	text,
    facebook_url	text,
    linkedin_url	text,
    twitter_url	text,
    logo_url	text,
    alias1	text,
    alias2	text,
    alias3	text,
    primary_role	text,
    num_exits	double precision
);

create table ${TABLE_PREFIX}_category_groups (
    uuid text primary key, 
    name text, 
    type text, 
    permalink text, 
    cb_url text, 
    rank double precision, 
    created_at timestamp, 
    updated_at timestamp,
    category_groups_list	text
);

create table ${TABLE_PREFIX}_people (
    uuid text primary key, 
    name text, 
    type text, 
    permalink text, 
    cb_url text, 
    rank double precision, 
    created_at timestamp, 
    updated_at timestamp,
    first_name text,
    last_name text,
    gender text,
    country_code text,
    state_code text,
    region text,
    city text,
    featured_job_organization_uuid text,
    featured_job_organization_name text,
    featured_job_title text,
    facebook_url text,
    linkedin_url text,
    twitter_url text,
    logo_url text
);

create table ${TABLE_PREFIX}_investors (
    uuid text primary key, 
    name text, 
    type text, 
    permalink text, 
    cb_url text, 
    rank double precision, 
    created_at timestamp, 
    updated_at timestamp,
    roles text,
    domain text,
    country_code text,
    state_code text,
    region text,
    city text,
    investor_types text,
    investment_count double precision,
    total_funding_usd double precision,
    total_funding double precision,
    total_funding_currency_code text,
    founded_on date,
    closed_on date,
    facebook_url text,
    linkedin_url text,
    twitter_url text,
    logo_url text
);

create table ${TABLE_PREFIX}_investments (
    uuid text primary key, 
    name text, 
    type text, 
    permalink text, 
    cb_url text, 
    rank double precision, 
    created_at timestamp, 
    updated_at timestamp,
    funding_round_uuid text,
    funding_round_name text,
    investor_uuid text,
    investor_name text,
    investor_type text,
    is_lead_investor boolean
);

create table ${TABLE_PREFIX}_funds (
    uuid text primary key, 
    name text, 
    type text, 
    permalink text, 
    cb_url text, 
    rank double precision, 
    created_at timestamp, 
    updated_at timestamp,
    entity_uuid text,
    entity_name text,
    entity_type text,
    announced_on date,
    raised_amount_usd double precision,
    raised_amount double precision,
    raised_amount_currency_code text
);

create table ${TABLE_PREFIX}_funding_rounds (
    uuid text primary key, 
    name text, 
    type text, 
    permalink text, 
    cb_url text, 
    rank double precision, 
    created_at timestamp, 
    updated_at timestamp,
    country_code text,
    state_code text,
    region text,
    city text,
    investment_type text,
    announced_on date,
    raised_amount_usd double precision, 	
    raised_amount double precision, 
    raised_amount_currency_code text,
    post_money_valuation_usd double precision, 
    post_money_valuation double precision, 
    post_money_valuation_currency_code text,
    investor_count double precision, 
    org_uuid text,
    org_name text,
    lead_investor_uuids text
);

EOT

# write copy statements 
for table in $TABLES; do
    for file in `{ ls ${table}.csv 2>/dev/null & ls ${table}_part_*.csv 2>/dev/null ;}`; do
        echo "\\copy ${TABLE_PREFIX}_${table} from '${PWD}/${file}' with delimiter as ',' csv header;" >> "$PSQL_SCRIPTNAME"
    done
done

# execute the script we just built
psql $DB_URL -f $PSQL_SCRIPTNAME

cd ..
